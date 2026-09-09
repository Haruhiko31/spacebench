from pygments.lexer import inherit
from .base import FileValidator, FileDescriptor, FileValidationResult, FileValidationError
from app.models.pod import FileType
import ast


class PythonValidator(FileValidator):
    ext = ".py"
    file_type = FileType.estimator

    def validate(self, file: FileDescriptor) -> FileValidationResult:
        issues: list[FileValidationError] = []

        print("-------------------------------------------------------------------------")
        print("[VALIDATION PY] STARTING VALIDATION...")
        print("-------------------------------------------------------------------------")

        # ═════════════════════════ FILE IS NOT EMPTY AND CAN BE READ

        lines, error = self.read_ascii_lines(file)

        if error:
            return error

        print(f"[VALIDATION PY] NOT_EMPTY : success !")
        print(f"[VALIDATION PY] BIN → TEXT : success !")

        source = "\n".join(lines)

        # Deploying Python file as Abstract Syntax Tree

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return self.send_error("PY_FILE_SYNTAX_ERROR", f"Python syntax error : {e.msg}", e.lineno or 0)

        print(f"[VALIDATION PY] AST PARSING : success !")

        print(ast.dump(tree, indent=4)) #DEBUG

        # ═════════════════════════ VERIFY CUSTOM ESTIMATOR CLASS EXISTENCE

        custom_estimator_class = None
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                if node.name == "CustomEstimator":
                    custom_estimator_class = node
                    break

        if custom_estimator_class is None:
            return self.send_error("PY_FILE_CUSTOM_ESTIMATOR_ERROR", f"There is no Custom estimator in the file", 0)

        print(f"[VALIDATION PY] CUSTOM ESTIMATOR EXISTENCE : success !")

        # ═════════════════════════ DOES THIS CLASS EXTEND BaseEstimator ?

        inherits_base_estimator = False
        for base in custom_estimator_class.bases:
            if isinstance(base, ast.Name):
                if base.id == "BaseEstimator":
                    inherits_base_estimator = True
                    break

        if not inherits_base_estimator:
            return self.send_error("PY_FILE_BASE_ESTIMATOR_ERROR", f"The Custom estimator does not extend BaseEstimator", 0)

        print(f"[VALIDATION PY] BASE ESTIMATOR EXTENSION : success !")

        # ═════════════════════════ VERIFY ESTIMATE() METHOD EXISTENCE

        has_estimate_method = False
        for fn in custom_estimator_class.body:
            if isinstance(fn, ast.FunctionDef):
                if fn.name == "estimate_epoch":
                    has_estimate_method = True

        if not has_estimate_method:
            return self.send_error("PY_FILE_ESTIMATE_METHOD_ERROR",f"There is no estimate method in the custom validator class", 0)

        print(f"[VALIDATION PY] ESTIMATE() METHOD : success !")

        forbidden_imports = {"os", "sys", "subprocess", "socket"}

        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_module = alias.name.split(".")[0]

                    if root_module in forbidden_imports:
                        return self.send_error("PY_FILE_FORBIDDEN_IMPORT", f"Forbidden import: {alias.name}", node.lineno)

            if isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    root_module = node.module.split(".")[0]

                    if root_module in forbidden_imports:
                        return self.send_error("PY_FILE_FORBIDDEN_IMPORT", f"Forbidden import: {node.module}", node.lineno)

        print(f"[VALIDATION PY] DANGEROUS IMPORTS : success !")

        forbiddens_calls = {"eval","exec","compile","__import__","open", "input"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):

                # body Calls
                if isinstance(node.func, ast.Name):
                    if node.func.id in forbiddens_calls:
                        return self.send_error(
                            "PY_FILE_FORBIDDEN_CALL",f"Forbidden function call: {node.func.id}", node.lineno)

                # functions Calls
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in forbiddens_calls:
                        return self.send_error( "PY_FILE_FORBIDDEN_CALL", f"Forbidden method call: {node.func.attr}", node.lineno)

        print(f"[VALIDATION PY] DANGEROUS CALLS : success !")


        print("-------------------------------------------------------------------------")
        print("[VALIDATION PY] SUCCESS")
        print("-------------------------------------------------------------------------")

        return FileValidationResult(
            valid=True,
            issues=issues
        )