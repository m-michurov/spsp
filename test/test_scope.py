from unittest.mock import patch

import pytest

from spsp import Scope
from spsp.errors import SpspNameError, SpspInvalidBindingTargetError


# noinspection DuplicatedCode
class TestScope:
    @pytest.mark.parametrize(
        'mutable',
        (
            True,
            False
        )
    )
    def test_bind(self, mutable: bool) -> None:
        # Arrange
        scope = Scope.empty()
        name, value = 'x', 42

        # Act
        scope.bind(name, value, mutable=mutable)
        obj = scope.value(name)

        # Assert
        assert obj == value

    def test_let(self) -> None:
        # Arrange
        scope = Scope.empty()
        name, value = 'x', 42

        # Act
        scope.let(name, value)
        obj = scope.value(name)

        # Assert
        assert obj == value

    def test_rebind(self) -> None:
        # Arrange
        scope = Scope.empty()
        name, value, new_value = 'x', 42, 43

        # Act
        scope.let(name, value)
        scope.let(name, new_value)
        obj = scope.value(name)

        # Assert
        assert obj == new_value

    def test_rebind_builtin(self) -> None:
        # Arrange
        scope = Scope.empty()
        name, new_value = 'print', lambda *args: None

        # Act
        scope.let(name, new_value)
        obj = scope.value(name)

        # Assert
        assert obj == new_value

    def test_rebind_keyword(self) -> None:
        # Arrange
        scope = Scope.empty()
        keyword = 'let'

        # Act & Assert
        with pytest.raises(SpspInvalidBindingTargetError):
            scope.let(keyword, None)

    def test_rebind_immutable_binding(self) -> None:
        # Arrange
        scope = Scope.empty()
        name = 'x'
        scope.bind(name, None, mutable=False)

        # Act & Assert
        with pytest.raises(SpspInvalidBindingTargetError):
            scope.let(name, None)

    def test_value_builtin(self) -> None:
        # Arrange
        scope = Scope.empty()
        name, value = 'print', print

        # Act
        obj = scope.value(name)

        # Assert
        assert obj == value

    def test_delete(self) -> None:
        # Arrange
        scope = Scope.empty()
        name, value = 'x', 42
        scope.let(name, value)

        # Act
        scope.delete(name)

        # Assert
        with pytest.raises(SpspNameError):
            scope.value(name)

    def test_delete_builtin(self) -> None:
        # Arrange
        scope = Scope.empty()
        name, value = 'print', print

        # Act
        scope.delete(name)
        obj = scope.value(name)

        # Assert
        assert obj == value

    def test_delete_rebound_builtin(self) -> None:
        # Arrange
        scope = Scope.empty()
        name, original_value, new_value = 'print', print, lambda *args: None

        scope.let(name, new_value)

        # Act
        scope.delete(name)
        obj = scope.value(name)

        # Assert
        assert obj == original_value

    def test_delete_keyword(self) -> None:
        # Arrange
        scope = Scope.empty()
        keyword = 'let'

        # Act & Assert
        with pytest.raises(SpspInvalidBindingTargetError):
            scope.delete(keyword)

    def test_let_in_derived(self) -> None:
        # Arrange
        scope = Scope.empty()
        derived_scope = scope.derive()
        name, value = 'x', 42

        # Act
        derived_scope.let(name, value)
        obj = derived_scope.value(name)

        # Assert
        assert obj == value
        with pytest.raises(SpspNameError):
            scope.value(name)

    def test_rebind_in_derived(self) -> None:
        # Arrange
        scope = Scope.empty()
        derived_scope = scope.derive()
        name, original_value, new_value = 'x', 42, 43

        scope.let(name, original_value)

        # Act
        derived_scope.let(name, new_value)
        original_obj = scope.value(name)
        derived_obj = derived_scope.value(name)

        # Assert
        assert original_obj == original_value
        assert derived_obj == new_value

    def test_import_module(self) -> None:
        # Arrange
        scope = Scope.empty()
        module_name = 'types'
        module_object = object()

        import importlib

        # Act
        with patch.object(importlib, 'import_module', return_value=module_object) as importlib_import_module:
            module = scope.import_module(module_name)

        # Assert
        assert module == module_object
        importlib_import_module.assert_called_once_with(module_name)

    def test_re_import_module(self) -> None:
        # Arrange
        scope = Scope.empty()
        module_name = 'types'
        scope.import_module(module_name)

        import types
        import importlib

        # Act
        with patch.object(importlib, 'import_module') as importlib_import_module:
            module = scope.import_module(module_name)

        # Assert
        assert module == types
        importlib_import_module.assert_not_called()

    def test_import_module_imported_in_parent(self) -> None:
        # Arrange
        scope = Scope.empty()
        derived_scope = scope.derive()
        module_name = 'types'
        scope.import_module(module_name)

        import types
        import importlib

        # Act
        with patch.object(importlib, 'import_module') as importlib_import_module:
            module = derived_scope.import_module(module_name)

        # Assert
        assert module == types
        importlib_import_module.assert_not_called()
