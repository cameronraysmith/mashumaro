from dataclasses import dataclass
from datetime import date, datetime
from typing import List

import pytest

from mashumaro import DataClassDictMixin
from mashumaro.config import ADD_DIALECT_SUPPORT, BaseConfig
from mashumaro.dialect import Dialect
from mashumaro.exceptions import BadDialect
from mashumaro.types import SerializationStrategy


class HexSerializationStrategy(SerializationStrategy):
    def serialize(self, value: int) -> str:
        return hex(value)

    def deserialize(self, value: str) -> int:
        return int(value, 16)


class OrdinalDialect(Dialect):
    serialization_strategy = {
        date: {
            "serialize": date.toordinal,
            "deserialize": date.fromordinal,
        },
        int: HexSerializationStrategy(),
    }


class FormattedDialect(Dialect):
    serialization_strategy = {
        date: {
            "serialize": lambda dt: dt.strftime("%Y/%m/%d"),
            "deserialize": lambda s: datetime.strptime(s, "%Y/%m/%d").date(),
        },
        int: HexSerializationStrategy(),
    }


class ISODialect(Dialect):
    serialization_strategy = {
        date: {
            "serialize": date.isoformat,
            "deserialize": date.fromisoformat,
        },
        int: HexSerializationStrategy(),
    }


@dataclass
class DataClassWithoutDialects(DataClassDictMixin):
    dt: date
    i: int


@dataclass
class DataClassWithDefaultDialect(DataClassDictMixin):
    dt: date
    i: int

    class Config(BaseConfig):
        dialect = OrdinalDialect


@dataclass
class DataClassWithDialectSupport(DataClassDictMixin):
    dt: date
    i: int

    class Config(BaseConfig):
        code_generation_options = [ADD_DIALECT_SUPPORT]


@dataclass
class DataClassWithDialectSupportAndDefaultDialect(DataClassDictMixin):
    dt: date
    i: int

    class Config(BaseConfig):
        code_generation_options = [ADD_DIALECT_SUPPORT]
        dialect = FormattedDialect
        debug = True


def test_default_dialect():
    dt = date.today()
    ordinal = dt.toordinal()
    obj = DataClassWithDefaultDialect(dt, 255)
    assert obj.to_dict() == {"dt": ordinal, "i": "0xff"}
    assert (
        DataClassWithDefaultDialect.from_dict({"dt": ordinal, "i": "0xff"})
        == obj
    )
    with pytest.raises(TypeError):
        obj.to_dict(dialect=OrdinalDialect)
    with pytest.raises(TypeError):
        DataClassWithDefaultDialect.from_dict(
            {"dt": ordinal, "i": "0xff"}, dialect=OrdinalDialect
        )


def test_dialect():
    dt = date.today()
    ordinal = dt.toordinal()
    obj = DataClassWithDialectSupport(dt, 255)
    assert obj.to_dict(dialect=OrdinalDialect) == {"dt": ordinal, "i": "0xff"}
    assert (
        DataClassWithDialectSupport.from_dict(
            {"dt": ordinal, "i": "0xff"}, dialect=OrdinalDialect
        )
        == obj
    )


def test_dialect_with_default():
    dt = date.today()
    ordinal = dt.toordinal()
    formatted = dt.strftime("%Y/%m/%d")
    obj = DataClassWithDialectSupportAndDefaultDialect(dt, 255)
    assert obj.to_dict() == {"dt": formatted, "i": "0xff"}
    assert (
        DataClassWithDialectSupportAndDefaultDialect.from_dict(
            {"dt": formatted, "i": "0xff"}
        )
        == obj
    )
    assert obj.to_dict(dialect=None) == {"dt": formatted, "i": "0xff"}
    assert (
        DataClassWithDialectSupportAndDefaultDialect.from_dict(
            {"dt": formatted, "i": "0xff"}, dialect=None
        )
        == obj
    )
    assert obj.to_dict(dialect=OrdinalDialect) == {"dt": ordinal, "i": "0xff"}
    assert (
        DataClassWithDialectSupportAndDefaultDialect.from_dict(
            {"dt": ordinal, "i": "0xff"}, dialect=OrdinalDialect
        )
        == obj
    )


def test_bad_default_dialect():
    with pytest.raises(BadDialect):

        @dataclass
        class _(DataClassDictMixin):
            dt: date

            class Config(BaseConfig):
                dialect = int


def test_bad_dialect():
    dt = date.today()
    ordinal = dt.toordinal()
    obj = DataClassWithDialectSupport(dt, 255)
    with pytest.raises(BadDialect):
        DataClassWithDialectSupport.from_dict(
            {"dt": ordinal, "i": "0xff"}, dialect=int
        )
    with pytest.raises(BadDialect):
        obj.to_dict(dialect=int)


def test_inner_without_dialects():
    @dataclass
    class DataClass(DataClassDictMixin):
        dt: date
        inner: DataClassWithoutDialects
        inners: List[DataClassWithoutDialects]
        i: int

        class Config(BaseConfig):
            code_generation_options = [ADD_DIALECT_SUPPORT]
            dialect = FormattedDialect

    dt = date.today()
    formatted = dt.strftime("%Y/%m/%d")
    ordinal = dt.toordinal()
    iso = dt.isoformat()
    obj = DataClass(
        dt=dt,
        inner=DataClassWithoutDialects(dt, 255),
        inners=[DataClassWithoutDialects(dt, 255)],
        i=255,
    )
    assert obj.to_dict() == {
        "dt": formatted,
        "inner": {"dt": iso, "i": 255},
        "inners": [{"dt": iso, "i": 255}],
        "i": "0xff",
    }
    assert obj.to_dict(dialect=OrdinalDialect) == {
        "dt": ordinal,
        "inner": {"dt": iso, "i": 255},
        "inners": [{"dt": iso, "i": 255}],
        "i": "0xff",
    }
    assert (
        DataClass.from_dict(
            {
                "dt": formatted,
                "inner": {"dt": iso, "i": 255},
                "inners": [{"dt": iso, "i": 255}],
                "i": "0xff",
            }
        )
        == obj
    )
    assert (
        DataClass.from_dict(
            {
                "dt": ordinal,
                "inner": {"dt": iso, "i": 255},
                "inners": [{"dt": iso, "i": 255}],
                "i": "0xff",
            },
            dialect=OrdinalDialect,
        )
        == obj
    )


def test_inner_with_default_dialect():
    @dataclass
    class DataClass(DataClassDictMixin):
        dt: date
        inner: DataClassWithDefaultDialect
        inners: List[DataClassWithDefaultDialect]
        i: int

        class Config(BaseConfig):
            code_generation_options = [ADD_DIALECT_SUPPORT]
            dialect = FormattedDialect

    dt = date.today()
    formatted = dt.strftime("%Y/%m/%d")
    ordinal = dt.toordinal()
    iso = dt.isoformat()
    obj = DataClass(
        dt=dt,
        inner=DataClassWithDefaultDialect(dt, 255),
        inners=[DataClassWithDefaultDialect(dt, 255)],
        i=255,
    )
    assert obj.to_dict() == {
        "dt": formatted,
        "inner": {"dt": ordinal, "i": "0xff"},
        "inners": [{"dt": ordinal, "i": "0xff"}],
        "i": "0xff",
    }
    assert obj.to_dict(dialect=ISODialect) == {
        "dt": iso,
        "inner": {"dt": ordinal, "i": "0xff"},
        "inners": [{"dt": ordinal, "i": "0xff"}],
        "i": "0xff",
    }
    assert (
        DataClass.from_dict(
            {
                "dt": formatted,
                "inner": {"dt": ordinal, "i": "0xff"},
                "inners": [{"dt": ordinal, "i": "0xff"}],
                "i": "0xff",
            }
        )
        == obj
    )
    assert (
        DataClass.from_dict(
            {
                "dt": iso,
                "inner": {"dt": ordinal, "i": "0xff"},
                "inners": [{"dt": ordinal, "i": "0xff"}],
                "i": "0xff",
            },
            dialect=ISODialect,
        )
        == obj
    )


def test_inner_with_dialect_support():
    @dataclass
    class DataClass(DataClassDictMixin):
        dt: date
        inner: DataClassWithDialectSupport
        inners: List[DataClassWithDialectSupport]
        i: int

        class Config(BaseConfig):
            code_generation_options = [ADD_DIALECT_SUPPORT]
            dialect = FormattedDialect

    dt = date.today()
    formatted = dt.strftime("%Y/%m/%d")
    iso = dt.isoformat()
    obj = DataClass(
        dt=dt,
        inner=DataClassWithDialectSupport(dt, 255),
        inners=[DataClassWithDialectSupport(dt, 255)],
        i=255,
    )
    assert obj.to_dict() == {
        "dt": formatted,
        "inner": {"dt": iso, "i": 255},
        "inners": [{"dt": iso, "i": 255}],
        "i": "0xff",
    }
    assert obj.to_dict(dialect=ISODialect) == {
        "dt": iso,
        "inner": {"dt": iso, "i": "0xff"},
        "inners": [{"dt": iso, "i": "0xff"}],
        "i": "0xff",
    }
    assert (
        DataClass.from_dict(
            {
                "dt": formatted,
                "inner": {"dt": iso, "i": 255},
                "inners": [{"dt": iso, "i": 255}],
                "i": "0xff",
            }
        )
        == obj
    )
    assert (
        DataClass.from_dict(
            {
                "dt": iso,
                "inner": {"dt": iso, "i": "0xff"},
                "inners": [{"dt": iso, "i": "0xff"}],
                "i": "0xff",
            },
            dialect=ISODialect,
        )
        == obj
    )


def test_inner_with_dialect_support_and_default():
    @dataclass
    class DataClass(DataClassDictMixin):
        dt: date
        inner: DataClassWithDialectSupportAndDefaultDialect
        inners: List[DataClassWithDialectSupportAndDefaultDialect]
        i: int

        class Config(BaseConfig):
            code_generation_options = [ADD_DIALECT_SUPPORT]
            dialect = FormattedDialect
            debug = False

    dt = date.today()
    formatted = dt.strftime("%Y/%m/%d")
    iso = dt.isoformat()
    obj = DataClass(
        dt=dt,
        inner=DataClassWithDialectSupportAndDefaultDialect(dt, 255),
        inners=[DataClassWithDialectSupportAndDefaultDialect(dt, 255)],
        i=255,
    )
    assert obj.to_dict() == {
        "dt": formatted,
        "inner": {"dt": formatted, "i": "0xff"},
        "inners": [{"dt": formatted, "i": "0xff"}],
        "i": "0xff",
    }
    assert obj.to_dict(dialect=ISODialect) == {
        "dt": iso,
        "inner": {"dt": iso, "i": "0xff"},
        "inners": [{"dt": iso, "i": "0xff"}],
        "i": "0xff",
    }
    assert (
        DataClass.from_dict(
            {
                "dt": formatted,
                "inner": {"dt": formatted, "i": "0xff"},
                "inners": [{"dt": formatted, "i": "0xff"}],
                "i": "0xff",
            }
        )
        == obj
    )
    assert (
        DataClass.from_dict(
            {
                "dt": iso,
                "inner": {"dt": iso, "i": "0xff"},
                "inners": [{"dt": iso, "i": "0xff"}],
                "i": "0xff",
            },
            dialect=ISODialect,
        )
        == obj
    )
