import re
from typing import Any, List, Dict, Pattern, Set, Callable, Union, Tuple
import math


def assert_equals(actual: Any, expected: Any, description: str = "Values should be equal"):
    """
    Asserts the two values are equal, or raises error including the provided description.
    
    Args:
        actual: The actual value to check
        expected: The expected value to compare against
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If actual != expected
    """
    assert actual == expected, f"{description}, expected: '{expected}' != actual: '{actual}'"


def assert_not_equals(actual: Any, expected: Any, description: str = "Values should not be equal"):
    """
    Asserts the two values are not equal, or raises error including the provided description.
    
    Args:
        actual: The actual value to check
        expected: The expected value to compare against
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If actual == expected
    """
    assert actual != expected, f"{description}, expected: '{expected}' == actual: '{actual}'"


def assert_true(condition: bool, description: str = "Condition should be true"):
    """
    Asserts the condition is True, or raises error including the provided description.
    
    Args:
        condition: The condition to check
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If condition is not True
    """
    assert condition is True, f"{description}, condition is {condition}"


def assert_false(condition: bool, description: str = "Condition should be false"):
    """
    Asserts the condition is False, or raises error including the provided description.
    
    Args:
        condition: The condition to check
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If condition is not False
    """
    assert condition is False, f"{description}, condition is {condition}"


def assert_is(actual: Any, expected: Any, description: str = "Objects should be the same"):
    """
    Asserts the two objects are the same object (using 'is'), or raises error including the description.
    
    Args:
        actual: The actual object
        expected: The expected object
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If actual is not expected
    """
    assert actual is expected, f"{description}, expected: '{expected}' is not actual: '{actual}'"


def assert_is_not(actual: Any, expected: Any, description: str = "Objects should not be the same"):
    """
    Asserts the two objects are not the same object (using 'is not'), or raises error including the description.
    
    Args:
        actual: The actual object
        expected: The expected object
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If actual is expected
    """
    assert actual is not expected, f"{description}, expected: '{expected}' is actual: '{actual}'"


def assert_is_none(value: Any, description: str = "Value should be None"):
    """
    Asserts the value is None, or raises error including the provided description.
    
    Args:
        value: The value to check
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If value is not None
    """
    assert value is None, f"{description}, value is {value}"


def assert_is_not_none(value: Any, description: str = "Value should not be None"):
    """
    Asserts the value is not None, or raises error including the provided description.
    
    Args:
        value: The value to check
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If value is None
    """
    assert value is not None, f"{description}, value is None"


def assert_in(item: Any, container: Union[List, Dict, Set, str, Tuple], 
             description: str = "Item should be in container"):
    """
    Asserts the item is in the container, or raises error including the provided description.
    
    Args:
        item: The item to check for
        container: The container to check in (list, dict, set, string, tuple)
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If item not in container
    """
    assert item in container, f"{description}, item '{item}' not found in: {container}"


def assert_not_in(item: Any, container: Union[List, Dict, Set, str, Tuple],
                 description: str = "Item should not be in container"):
    """
    Asserts the item is not in the container, or raises error including the provided description.
    
    Args:
        item: The item to check for
        container: The container to check in (list, dict, set, string, tuple)
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If item in container
    """
    assert item not in container, f"{description}, item '{item}' found in: {container}"


def assert_list_equals(actual: List, expected: List, description: str = "Lists should be equal"):
    """
    Asserts the two lists are equal (same elements in same order), or raises error including the description.
    
    Args:
        actual: The actual list
        expected: The expected list
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If lists are not equal
    """
    assert actual == expected, f"{description}, expected: {expected} != actual: {actual}"


def assert_list_contains_same(actual: List, expected: List, 
                             description: str = "Lists should contain the same elements"):
    """
    Asserts the two lists contain the same elements (order doesn't matter), or raises error.
    
    Args:
        actual: The actual list
        expected: The expected list
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If lists don't contain the same elements
    """
    missing = [item for item in expected if item not in actual]
    extra = [item for item in actual if item not in expected]
    
    assert not missing and not extra, (
        f"{description}, lists differ: "
        f"missing from actual: {missing if missing else 'none'}, "
        f"extra in actual: {extra if extra else 'none'}"
    )


def assert_list_subset(subset: List, superset: List, 
                      description: str = "First list should be a subset of second list"):
    """
    Asserts the first list is a subset of the second list, or raises error.
    
    Args:
        subset: The list that should be a subset
        superset: The list that should be a superset
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If subset is not a subset of superset
    """
    missing = [item for item in subset if item not in superset]
    assert not missing, f"{description}, items not in superset: {missing}"


def assert_dict_equals(actual: Dict, expected: Dict, description: str = "Dictionaries should be equal"):
    """
    Asserts the two dictionaries are equal, or raises error including the description.
    
    Args:
        actual: The actual dictionary
        expected: The expected dictionary
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If dictionaries are not equal
    """
    assert actual == expected, (
        f"{description}, dictionaries differ: "
        f"expected: {expected} != actual: {actual}"
    )


def assert_dict_contains_subset(subset: Dict, superset: Dict, 
                               description: str = "First dict should be a subset of second dict"):
    """
    Asserts the first dictionary is a subset of the second dictionary, or raises error.
    
    Args:
        subset: The dictionary that should be a subset
        superset: The dictionary that should be a superset
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If subset is not a subset of superset
    """
    missing_keys = [key for key in subset if key not in superset]
    different_values = [key for key in subset if key in superset and subset[key] != superset[key]]
    
    assert not missing_keys and not different_values, (
        f"{description}, dictionary subset check failed: "
        f"missing keys: {missing_keys if missing_keys else 'none'}, "
        f"different values for keys: {different_values if different_values else 'none'}"
    )


def assert_dict_has_keys(dictionary: Dict, keys: List, 
                        description: str = "Dictionary should have specified keys"):
    """
    Asserts the dictionary has all the specified keys, or raises error.
    
    Args:
        dictionary: The dictionary to check
        keys: The keys that should be present
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If dictionary doesn't have all the keys
    """
    missing_keys = [key for key in keys if key not in dictionary]
    assert not missing_keys, f"{description}, missing keys: {missing_keys}"


def assert_instance_of(obj: Any, class_or_tuple: Union[type, Tuple[type, ...]], 
                      description: str = "Object should be an instance of specified type(s)"):
    """
    Asserts the object is an instance of the specified class or classes, or raises error.
    
    Args:
        obj: The object to check
        class_or_tuple: The class or tuple of classes to check against
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If obj is not an instance of class_or_tuple
    """
    assert isinstance(obj, class_or_tuple), (
        f"{description}, expected instance of {class_or_tuple.__name__ if isinstance(class_or_tuple, type) else class_or_tuple}, "
        f"got {type(obj).__name__}"
    )


def assert_raises(exception_cls: type, callable_obj: Callable, *args, **kwargs):
    """
    Asserts that calling the callable with the given arguments raises the specified exception.
    
    Args:
        exception_cls: The exception class that should be raised
        callable_obj: The callable to execute
        *args: Positional arguments to pass to the callable
        **kwargs: Keyword arguments to pass to the callable
        
    Returns:
        The raised exception if it matches the expected type
        
    Raises:
        AssertionError: If the expected exception isn't raised or a different exception is raised
    """
    try:
        callable_obj(*args, **kwargs)
    except Exception as e:
        if isinstance(e, exception_cls):
            return e
        raise AssertionError(f"Expected {exception_cls.__name__}, but got {type(e).__name__}: {str(e)}")
    
    raise AssertionError(f"Expected {exception_cls.__name__} to be raised, but no exception was raised")


def assert_regex_match(text: str, pattern: Union[str, Pattern], 
                     description: str = "Text should match regex pattern"):
    """
    Asserts the text matches the regex pattern, or raises error.
    
    Args:
        text: The text to check
        pattern: The regex pattern to match against (string or compiled pattern)
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If text doesn't match pattern
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    
    assert pattern.search(text), f"{description}, text '{text}' doesn't match pattern '{pattern.pattern}'"


def assert_regex_not_match(text: str, pattern: Union[str, Pattern], 
                          description: str = "Text should not match regex pattern"):
    """
    Asserts the text doesn't match the regex pattern, or raises error.
    
    Args:
        text: The text to check
        pattern: The regex pattern to match against (string or compiled pattern)
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If text matches pattern
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    
    assert not pattern.search(text), f"{description}, text '{text}' matches pattern '{pattern.pattern}'"


def assert_float_equals(actual: float, expected: float, places: int = 7, 
                       description: str = "Float values should be equal"):
    """
    Asserts the two float values are equal up to a certain number of decimal places, or raises error.
    
    Args:
        actual: The actual float value
        expected: The expected float value
        places: The number of decimal places to check equality up to
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If floats are not equal up to places decimal places
    """
    assert round(abs(expected - actual), places) == 0, (
        f"{description}, expected: {expected} != actual: {actual}, "
        f"difference: {abs(expected - actual)}, places: {places}"
    )


def assert_float_almost_equals(actual: float, expected: float, rel_tol: float = 1e-9, abs_tol: float = 0.0,
                             description: str = "Float values should be almost equal"):
    """
    Asserts the two float values are almost equal (within tolerances), or raises error.
    Uses math.isclose() for the comparison.
    
    Args:
        actual: The actual float value
        expected: The expected float value
        rel_tol: The relative tolerance (default 1e-9)
        abs_tol: The absolute tolerance (default 0.0)
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If floats are not almost equal
    """
    assert math.isclose(actual, expected, rel_tol=rel_tol, abs_tol=abs_tol), (
        f"{description}, expected: {expected} != actual: {actual}, "
        f"difference: {abs(expected - actual)}, rel_tol: {rel_tol}, abs_tol: {abs_tol}"
    )


def assert_length_equals(obj: Union[List, Dict, Set, str, Tuple], length: int,
                         description: str = "Object should have specified length"):
    """
    Asserts the object has the specified length, or raises error.
    
    Args:
        obj: The object to check the length of
        length: The expected length
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If object doesn't have the specified length
    """
    assert len(obj) == length, f"{description}, expected length: {length}, actual length: {len(obj)}"


def assert_starts_with(text: str, prefix: str, description: str = "String should start with prefix"):
    """
    Asserts the string starts with the specified prefix, or raises error.
    
    Args:
        text: The string to check
        prefix: The prefix to check for
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If string doesn't start with prefix
    """
    assert text.startswith(prefix), f"{description}, '{text}' doesn't start with '{prefix}'"


def assert_ends_with(text: str, suffix: str, description: str = "String should end with suffix"):
    """
    Asserts the string ends with the specified suffix, or raises error.
    
    Args:
        text: The string to check
        suffix: The suffix to check for
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If string doesn't end with suffix
    """
    assert text.endswith(suffix), f"{description}, '{text}' doesn't end with '{suffix}'"


def assert_contains_text(text: str, substring: str, description: str = "String should contain substring"):
    """
    Asserts the string contains the specified substring, or raises error.
    
    Args:
        text: The string to check
        substring: The substring to check for
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If string doesn't contain substring
    """
    assert substring in text, f"{description}, '{text}' doesn't contain '{substring}'"


def assert_greater_than(actual: Any, expected: Any, description: str = "Value should be greater than expected"):
    """
    Asserts the actual value is greater than the expected value, or raises error.
    
    Args:
        actual: The actual value
        expected: The expected value
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If actual is not greater than expected
    """
    assert actual > expected, f"{description}, {actual} is not greater than {expected}"


def assert_greater_than_or_equal(actual: Any, expected: Any, 
                                description: str = "Value should be greater than or equal to expected"):
    """
    Asserts the actual value is greater than or equal to the expected value, or raises error.
    
    Args:
        actual: The actual value
        expected: The expected value
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If actual is not greater than or equal to expected
    """
    assert actual >= expected, f"{description}, {actual} is not greater than or equal to {expected}"


def assert_less_than(actual: Any, expected: Any, description: str = "Value should be less than expected"):
    """
    Asserts the actual value is less than the expected value, or raises error.
    
    Args:
        actual: The actual value
        expected: The expected value
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If actual is not less than expected
    """
    assert actual < expected, f"{description}, {actual} is not less than {expected}"


def assert_less_than_or_equal(actual: Any, expected: Any, 
                             description: str = "Value should be less than or equal to expected"):
    """
    Asserts the actual value is less than or equal to the expected value, or raises error.
    
    Args:
        actual: The actual value
        expected: The expected value
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If actual is not less than or equal to expected
    """
    assert actual <= expected, f"{description}, {actual} is not less than or equal to {expected}"


def assert_sorted(items: List, reverse: bool = False, description: str = "List should be sorted"):
    """
    Asserts the list is sorted, or raises error.
    
    Args:
        items: The list to check
        reverse: Whether to check for reverse sorting (default: False)
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If list is not sorted
    """
    sorted_items = sorted(items, reverse=reverse)
    assert items == sorted_items, f"{description}, list is not sorted: {items}"


def assert_json_schema_valid(instance: Any, schema: Dict, description: str = "JSON should validate against schema"):
    """
    Asserts the instance validates against the JSON schema, or raises error.
    Requires 'jsonschema' package to be installed.
    
    Args:
        instance: The instance to validate (typically a dict or list)
        schema: The JSON schema to validate against
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If instance doesn't validate against schema
        ImportError: If jsonschema package is not installed
    """
    try:
        import jsonschema
    except ImportError:
        raise ImportError("The 'jsonschema' package is required for assert_json_schema_valid()")
    
    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        raise AssertionError(f"{description}, validation error: {str(e)}")


def assert_subclass_of(cls: type, parent_cls: Union[type, Tuple[type, ...]],
                      description: str = "Class should be a subclass of parent class"):
    """
    Asserts the class is a subclass of the parent class, or raises error.
    
    Args:
        cls: The class to check
        parent_cls: The parent class or tuple of parent classes
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If cls is not a subclass of parent_cls
    """
    assert issubclass(cls, parent_cls), (
        f"{description}, {cls.__name__} is not a subclass of "
        f"{parent_cls.__name__ if isinstance(parent_cls, type) else parent_cls}"
    )


def assert_dict_values_are_instance_of(dictionary: Dict, 
                                      value_type: Union[type, Tuple[type, ...]], 
                                      description: str = "Dictionary values should be of specified type"):
    """
    Asserts all values in the dictionary are instances of the specified type, or raises error.
    
    Args:
        dictionary: The dictionary to check
        value_type: The type or tuple of types that values should be
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If any value is not an instance of value_type
    """
    invalid_items = {k: type(v).__name__ for k, v in dictionary.items() if not isinstance(v, value_type)}
    assert not invalid_items, (
        f"{description}, the following items have incorrect types: {invalid_items}, "
        f"expected type: {value_type.__name__ if isinstance(value_type, type) else value_type}"
    )


def assert_list_items_are_instance_of(items: List, 
                                     item_type: Union[type, Tuple[type, ...]], 
                                     description: str = "List items should be of specified type"):
    """
    Asserts all items in the list are instances of the specified type, or raises error.
    
    Args:
        items: The list to check
        item_type: The type or tuple of types that items should be
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If any item is not an instance of item_type
    """
    invalid_items = [(i, type(item).__name__) for i, item in enumerate(items) if not isinstance(item, item_type)]
    assert not invalid_items, (
        f"{description}, the following items have incorrect types: {invalid_items}, "
        f"expected type: {item_type.__name__ if isinstance(item_type, type) else item_type}"
    )


def assert_directories_equal(dir1: str, dir2: str, 
                            description: str = "Directories should have the same structure and content"):
    """
    Asserts two directories have the same structure and file contents, or raises error.
    
    Args:
        dir1: Path to first directory
        dir2: Path to second directory
        description: Description of the assertion for the error message
    
    Raises:
        AssertionError: If directories are not equal
    """
    import os
    import filecmp
    
    # Check both paths are directories
    assert os.path.isdir(dir1), f"{dir1} is not a directory"
    assert os.path.isdir(dir2), f"{dir2} is not a directory"
    
    comparison = filecmp.dircmp(dir1, dir2)
    
    # Check for differences
    differences = []
    if comparison.left_only:
        differences.append(f"Files only in {dir1}: {comparison.left_only}")
    if comparison.right_only:
        differences.append(f"Files only in {dir2}: {comparison.right_only}")
    if comparison.diff_files:
        differences.append(f"Files differing: {comparison.diff_files}")
    if comparison.funny_files:
        differences.append(f"Files that could not be compared: {comparison.funny_files}")
    
    assert not differences, f"{description}, {', '.join(differences)}"