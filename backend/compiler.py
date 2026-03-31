"""
Code Execution Module for Competitive Programming
Handles safe compilation and execution of C code with test cases.
"""
import os
import subprocess
import tempfile
import signal
from pathlib import Path
from typing import Optional

# Execution limits
TIME_LIMIT = 5  # seconds
MEMORY_LIMIT = 256  # MB
OUTPUT_SIZE_LIMIT = 10000  # chars

class CompilationError(Exception):
    """Raised when code compilation fails"""
    pass

class ExecutionError(Exception):
    """Raised when code execution fails"""
    pass

class TimeoutError(Exception):
    """Raised when execution exceeds time limit"""
    pass

def compile_c_code(code: str, timeout: int = 10) -> str:
    """
    Compile C code and return path to executable.
    
    Args:
        code: C source code as string
        timeout: Compilation timeout in seconds
        
    Returns:
        Path to compiled executable
        
    Raises:
        CompilationError: If compilation fails
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        source_file = tmpdir_path / "code.c"
        executable = tmpdir_path / "code.out"
        
        # Write source code to file
        source_file.write_text(code)
        
        try:
            # Compile with gcc
            compile_cmd = [
                "gcc",
                "-o", str(executable),
                str(source_file),
                "-lm",  # Link math library
                "-std=c99",  # Use C99 standard
                "-Wall",  # Show all warnings
            ]
            
            result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown compilation error"
                raise CompilationError(f"Compilation failed:\n{error_msg}")
            
            # Copy executable to persistent location
            exec_dir = Path(__file__).parent / "exec_cache"
            exec_dir.mkdir(exist_ok=True)
            import uuid
            exec_name = f"code_{uuid.uuid4().hex}.out"
            persistent_exec = exec_dir / exec_name
            
            with open(executable, 'rb') as src:
                persistent_exec.write_bytes(src.read())
            
            return str(persistent_exec)
            
        except subprocess.TimeoutExpired:
            raise CompilationError("Compilation timeout exceeded")
        except Exception as e:
            raise CompilationError(f"Compilation error: {str(e)}")

def execute_code(executable_path: str, input_data: str = "", timeout: int = TIME_LIMIT) -> str:
    """
    Execute compiled C code with given input.
    
    Args:
        executable_path: Path to compiled executable
        input_data: Standard input for the program
        timeout: Execution timeout in seconds
        
    Returns:
        Program output (stdout)
        
    Raises:
        ExecutionError: If execution fails
        TimeoutError: If execution exceeds timeout
    """
    try:
        result = subprocess.run(
            [executable_path],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = result.stdout[:OUTPUT_SIZE_LIMIT]
        
        if result.returncode != 0 and result.stderr:
            raise ExecutionError(f"Runtime error:\n{result.stderr[:OUTPUT_SIZE_LIMIT]}")
        
        return output
        
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Execution exceeded {timeout}s timeout")
    except Exception as e:
        raise ExecutionError(f"Execution error: {str(e)}")

def cleanup_executable(executable_path: str):
    """Remove compiled executable to free space"""
    try:
        if os.path.exists(executable_path):
            os.remove(executable_path)
    except Exception:
        pass  # Ignore cleanup errors

def test_code(code: str, test_cases: list[dict]) -> dict:
    """
    Compile and test C code against multiple test cases.
    
    Args:
        code: C source code
        test_cases: List of dicts with 'input' and 'expected_output' keys
        
    Returns:
        Dict with overall results and per-test details
    """
    try:
        # Compile code
        executable = compile_c_code(code)
    except CompilationError as e:
        return {
            "status": "COMPILATION_ERROR",
            "message": str(e),
            "passed": 0,
            "total": len(test_cases),
            "results": []
        }
    
    results = []
    passed = 0
    
    try:
        for idx, test_case in enumerate(test_cases):
            test_input = test_case.get("input", "")
            expected = test_case.get("expected_output", "").strip()
            
            try:
                actual = execute_code(executable, test_input).strip()
                
                if actual == expected:
                    results.append({
                        "test_case": idx + 1,
                        "status": "PASS",
                        "input": test_input[:200],
                        "expected": expected[:200],
                        "actual": actual[:200],
                    })
                    passed += 1
                else:
                    results.append({
                        "test_case": idx + 1,
                        "status": "FAIL",
                        "input": test_input[:200],
                        "expected": expected[:200],
                        "actual": actual[:200],
                    })
                    
            except (ExecutionError, TimeoutError) as e:
                results.append({
                    "test_case": idx + 1,
                    "status": "RUNTIME_ERROR" if isinstance(e, ExecutionError) else "TIMEOUT",
                    "input": test_input[:200],
                    "error": str(e),
                })
    
    finally:
        cleanup_executable(executable)
    
    return {
        "status": "ACCEPTED" if passed == len(test_cases) else "PARTIAL",
        "passed": passed,
        "total": len(test_cases),
        "results": results,
    }
