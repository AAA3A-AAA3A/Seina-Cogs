"""
MIT License

Copyright (c) 2022-present japandotorg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Any, ClassVar

class HasDescriptionCode:
    code: str | None
    def __init__(self, *arg: Any, code: str | None = ..., **kw: Any) -> None: ...

class SQLAlchemyError(HasDescriptionCode, Exception):
    def __unicode__(self) -> str: ...

class ArgumentError(SQLAlchemyError): ...

class ObjectNotExecutableError(ArgumentError):
    target: Any
    def __init__(self, target) -> None: ...
    def __reduce__(self): ...

class NoSuchModuleError(ArgumentError): ...
class NoForeignKeysError(ArgumentError): ...
class AmbiguousForeignKeysError(ArgumentError): ...

class CircularDependencyError(SQLAlchemyError):
    cycles: Any
    edges: Any
    def __init__(
        self, message, cycles, edges, msg: Any | None = ..., code: Any | None = ...
    ) -> None: ...
    def __reduce__(self): ...

class CompileError(SQLAlchemyError): ...

class UnsupportedCompilationError(CompileError):
    code: str
    compiler: Any
    element_type: Any
    message: str | None
    def __init__(self, compiler, element_type, message: str | None = ...) -> None: ...
    def __reduce__(self): ...

class IdentifierError(SQLAlchemyError): ...

class DisconnectionError(SQLAlchemyError):
    invalidate_pool: bool

class InvalidatePoolError(DisconnectionError):
    invalidate_pool: bool

class TimeoutError(SQLAlchemyError): ...
class InvalidRequestError(SQLAlchemyError): ...
class NoInspectionAvailable(InvalidRequestError): ...
class PendingRollbackError(InvalidRequestError): ...
class ResourceClosedError(InvalidRequestError): ...
class NoSuchColumnError(InvalidRequestError, KeyError): ...
class NoResultFound(InvalidRequestError): ...
class MultipleResultsFound(InvalidRequestError): ...
class NoReferenceError(InvalidRequestError): ...

class AwaitRequired(InvalidRequestError):
    code: str

class MissingGreenlet(InvalidRequestError):
    code: str

class NoReferencedTableError(NoReferenceError):
    table_name: Any
    def __init__(self, message, tname) -> None: ...
    def __reduce__(self): ...

class NoReferencedColumnError(NoReferenceError):
    table_name: Any
    column_name: Any
    def __init__(self, message, tname, cname) -> None: ...
    def __reduce__(self): ...

class NoSuchTableError(InvalidRequestError): ...
class UnreflectableTableError(InvalidRequestError): ...
class UnboundExecutionError(InvalidRequestError): ...
class DontWrapMixin: ...

class StatementError(SQLAlchemyError):
    statement: Any
    params: Any
    orig: Any
    ismulti: Any
    hide_parameters: Any
    detail: Any
    def __init__(
        self,
        message,
        statement,
        params,
        orig,
        hide_parameters: bool = ...,
        code: Any | None = ...,
        ismulti: Any | None = ...,
    ) -> None: ...
    def add_detail(self, msg) -> None: ...
    def __reduce__(self): ...

class DBAPIError(StatementError):
    code: str
    @classmethod
    def instance(
        cls,
        statement,
        params,
        orig,
        dbapi_base_err,
        hide_parameters: bool = ...,
        connection_invalidated: bool = ...,
        dialect: Any | None = ...,
        ismulti: Any | None = ...,
    ): ...
    def __reduce__(self): ...
    connection_invalidated: Any
    def __init__(
        self,
        statement,
        params,
        orig,
        hide_parameters: bool = ...,
        connection_invalidated: bool = ...,
        code: Any | None = ...,
        ismulti: Any | None = ...,
    ) -> None: ...

class InterfaceError(DBAPIError): ...
class DatabaseError(DBAPIError): ...
class DataError(DatabaseError): ...
class OperationalError(DatabaseError): ...
class IntegrityError(DatabaseError): ...
class InternalError(DatabaseError): ...
class ProgrammingError(DatabaseError): ...
class NotSupportedError(DatabaseError): ...

class SADeprecationWarning(HasDescriptionCode, DeprecationWarning):
    deprecated_since: ClassVar[str | None]

class Base20DeprecationWarning(SADeprecationWarning):
    deprecated_since: ClassVar[str]

class LegacyAPIWarning(Base20DeprecationWarning): ...
class RemovedIn20Warning(Base20DeprecationWarning): ...
class MovedIn20Warning(RemovedIn20Warning): ...

class SAPendingDeprecationWarning(PendingDeprecationWarning):
    deprecated_since: ClassVar[str | None]

class SAWarning(HasDescriptionCode, RuntimeWarning): ...