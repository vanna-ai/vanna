"""
Development utilities for validating Pydantic models.

This module provides utilities that can be used during development
and testing to catch forward reference issues early.
"""

from typing import Any, Dict, List, Tuple, Type
from pydantic import BaseModel
import importlib
import inspect


def validate_pydantic_models_in_package(package_name: str) -> Dict[str, Any]:
    """
    Validate all Pydantic models in a package for completeness.
    
    This function can be used in tests or development scripts to catch
    forward reference issues before they cause runtime errors.
    
    Args:
        package_name: Name of the package to validate (e.g., 'vanna.core')
        
    Returns:
        Dictionary with validation results
    """
    results: Dict[str, Any] = {
        'total_models': 0,
        'incomplete_models': [],
        'models': {},
        'summary': ''
    }
    
    try:
        # Import the package
        package = importlib.import_module(package_name)
        
        # Get all submodules
        submodules = []
        if hasattr(package, '__path__'):
            import pkgutil
            for _, name, _ in pkgutil.iter_modules(package.__path__, package_name + '.'):
                try:
                    submodule = importlib.import_module(name)
                    submodules.append((name, submodule))
                except ImportError:
                    continue
        else:
            submodules = [(package_name, package)]
        
        # Check all Pydantic models in each submodule
        for module_name, module in submodules:
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseModel) and 
                    obj is not BaseModel):
                    
                    model_key = f"{module_name}.{name}"
                    results['total_models'] += 1
                    
                    # Check for forward references
                    forward_refs: List[Tuple[str, str]] = []
                    for field_name, field_info in obj.model_fields.items():
                        annotation = field_info.annotation
                        if annotation is not None and hasattr(annotation, '__forward_arg__'):
                            forward_refs.append((field_name, annotation.__forward_arg__))
                    
                    # Check completeness
                    try:
                        obj.model_json_schema()
                        is_complete = True
                        error = None
                    except Exception as e:
                        is_complete = False
                        error = str(e)
                        results['incomplete_models'].append(model_key)
                    
                    results['models'][model_key] = {
                        'class': obj,
                        'forward_references': forward_refs,
                        'is_complete': is_complete,
                        'error': error
                    }
        
        # Generate summary
        incomplete_models = results['incomplete_models']
        incomplete_count = len(incomplete_models)
        total_models = results['total_models']
        if incomplete_count == 0:
            results['summary'] = f"✓ All {total_models} Pydantic models are complete and valid!"
        else:
            results['summary'] = (f"⚠ {incomplete_count} of {total_models} models are incomplete: "
                                f"{', '.join(incomplete_models)}")
        
    except Exception as e:
        results['summary'] = f"Error validating package {package_name}: {e}"
    
    return results


def check_models_health() -> bool:
    """
    Quick health check for all core Pydantic models.
    
    Returns:
        True if all models are healthy, False otherwise
    """
    core_packages = [
        'vanna.core.tool.models',
        'vanna.core.user.models',
        'vanna.core.llm.models',
        'vanna.core.storage.models',
        'vanna.core.agent.models',
    ]
    
    all_healthy = True
    
    for package in core_packages:
        try:
            results = validate_pydantic_models_in_package(package)
            if results['incomplete_models']:
                print(f"❌ Issues in {package}: {results['incomplete_models']}")
                all_healthy = False
            else:
                print(f"✅ {package}: {results['total_models']} models OK")
        except Exception as e:
            print(f"❌ Error checking {package}: {e}")
            all_healthy = False
    
    return all_healthy


if __name__ == "__main__":
    print("Checking Pydantic model health across core packages...")
    print("=" * 60)
    
    healthy = check_models_health()
    
    print("=" * 60)
    if healthy:
        print("🎉 All Pydantic models are healthy!")
    else:
        print("⚠️  Some models need attention.")
        print("\nTo fix forward reference issues:")
        print("1. Ensure all referenced classes are imported")
        print("2. Call model_rebuild() after imports")
        print("3. Use proper TYPE_CHECKING imports for circular deps")
    
    print("\nNote: You can also catch these issues at development time using:")
    print("  - mypy static type checking")
    print("  - This validation script in your test suite")
    print("  - Pre-commit hooks")