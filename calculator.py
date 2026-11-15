import sys
import ast
import math
import operator
import re

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QDialog, QFrame
)

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont


# ==========================================
# МАТЕМАТИЧЕСКИЙ ДВИЖОК
# ==========================================

def calculate(expression):

    operations = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos
    }

    def evaluate(node):

        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                return node.value

        elif isinstance(node, ast.BinOp):
            op = type(node.op)

            if op in operations:
                left = evaluate(node.left)
                right = evaluate(node.right)

                if op == ast.Pow and abs(right) > 1000:
                    raise ValueError("Слишком большая степень")

                return operations[op](left, right)

        elif isinstance(node, ast.UnaryOp):
            op = type(node.op)

            if op in operations:
                return operations[op](evaluate(node.operand))

        raise ValueError("Недопустимое выражение")

    result = evaluate(
        ast.parse(expression, mode="eval").body
    )

    if not math.isfinite(result):
        raise ValueError("Некорректный результат")

    if abs(result) > 1e100:
        raise ValueError("Слишком большое число")

    return result


# ==========================================
# ТЕМЫ
# ==========================================

THEMES = {

    "dark": {
        "panel": "rgba(20,20,20,175)",
        "border": "rgba(255,255,255,90)",
        "text": "#ffffff",
        "button": "rgba(255,255,255,0)",
        "hover": "rgba(255,255,255,40)",
        "operator": "rgba(255,255,255,45)",
        "operator_hover": "rgba(255,255,255,90)",
        "footer": "rgba(255,255,255,160)",
        "settings": "rgba(30,30,30,245)"
    },

    "light": {
        "panel": "rgba(255,255,255,175)",
        "border": "rgba(255,255,255,220)",
        "text": "#202020",
        "button": "rgba(255,255,255,0)",
        "hover": "rgba(255,255,255,120)",
        "operator": "rgba(255,255,255,150)",
        "operator_hover": "rgba(255,255,255,220)",
        "footer": "rgba(0,0,0,150)",
        "settings": "rgba(245,245,245,245)"
    }
}


# ==========================================
# ВЕРХНЯЯ ПАНЕЛЬ
# ==========================================

class DragBar(QWidget):

    def __init__(self, parent):

        super().__init__(parent)

        self.window = parent
        self.drag_position = None

        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(7)

        self.title = QLabel("LIQUID GLASS")

        self.title.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

        self.title.setFont(
            QFont("Segoe UI", 11, QFont.Weight.Bold)
        )

        layout.addWidget(self.title)
        layout.addStretch()

        self.settings_btn = QPushButton("⚙")
        self.min_btn = QPushButton("−")
        self.close_btn = QPushButton("×")

        for button in (
            self.settings_btn,
            self.min_btn,
            self.close_btn
        ):
            button.setFixedSize(32, 32)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.settings_btn.clicked.connect(
            self.window.open_settings
        )

        self.min_btn.clicked.connect(
            self.window.showMinimized
        )

        self.close_btn.clicked.connect(
            self.window.close
        )

        layout.addWidget(self.settings_btn)
        layout.addWidget(self.min_btn)
        layout.addWidget(self.close_btn)

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            self.drag_position = (
                event.globalPosition().toPoint()
                - self.window.frameGeometry().topLeft()
            )

            event.accept()

    def mouseMoveEvent(self, event):

        if (
            self.drag_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):

            self.window.move(
                event.globalPosition().toPoint()
                - self.drag_position
            )

            event.accept()

    def mouseReleaseEvent(self, event):

        self.drag_position = None
        event.accept()


# ==========================================
# НАСТРОЙКИ
# ==========================================

class SettingsDialog(QDialog):

    def __init__(self, parent):

        super().__init__(parent)

        self.calculator = parent

        self.setWindowTitle("Настройки")
        self.setFixedSize(285, 220)

        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)

        self.panel = QFrame()
        self.panel.setObjectName("settingsPanel")

        main.addWidget(self.panel)

        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.title = QLabel("НАСТРОЙКИ")

        self.title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.title.setFont(
            QFont("Segoe UI", 13, QFont.Weight.Bold)
        )

        layout.addWidget(self.title)

        self.dark_btn = QPushButton("⚫  Чёрная тема")
        self.light_btn = QPushButton("⚪  Белая тема")
        self.done_btn = QPushButton("Готово")

        self.dark_btn.setFixedHeight(40)
        self.light_btn.setFixedHeight(40)
        self.done_btn.setFixedHeight(35)

        layout.addWidget(self.dark_btn)
        layout.addWidget(self.light_btn)
        layout.addWidget(self.done_btn)

        self.dark_btn.clicked.connect(
            lambda: self.select_theme("dark")
        )

        self.light_btn.clicked.connect(
            lambda: self.select_theme("light")
        )

        self.done_btn.clicked.connect(self.accept)

        self.apply_style()

    def select_theme(self, theme):

        self.calculator.apply_theme(theme)
        self.apply_style()

    def apply_style(self):

        c = THEMES[self.calculator.theme]

        self.panel.setStyleSheet(f"""
            QFrame#settingsPanel {{
                background: {c['settings']};
                border: 1px solid {c['border']};
                border-radius: 25px;
            }}
        """)

        self.title.setStyleSheet(f"""
            color: {c['text']};
            background: transparent;
            border: none;
        """)

        for button in (
            self.dark_btn,
            self.light_btn,
            self.done_btn
        ):

            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

            button.setStyleSheet(f"""
                QPushButton {{
                    background: {c['button']};
                    color: {c['text']};
                    border: 1px solid {c['border']};
                    border-radius: 12px;
                    font-size: 13px;
                }}

                QPushButton:hover {{
                    background: {c['hover']};
                }}
            """)


# ==========================================
# ГЛАВНЫЙ КАЛЬКУЛЯТОР
# ==========================================

class GlassCalculator(QWidget):

    def __init__(self):

        super().__init__()

        self.expression = ""
        self.theme = "dark"
        self.buttons = []

        self.just_calculated = False

        # Последняя операция для повторного "="
        self.last_operator = None
        self.last_operand = None

        self.settings = QSettings(
            "RapiraStudio",
            "LiquidGlassCalculator"
        )

        self.setWindowTitle("Liquid Glass Calculator")
        self.setFixedSize(430, 730)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Window
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

        # Главная панель

        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)

        self.panel = QFrame()
        self.panel.setObjectName("glassPanel")

        main.addWidget(self.panel)

        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        # Верхняя панель

        self.drag_bar = DragBar(self)
        layout.addWidget(self.drag_bar)

        # Строка выражения

        expression_row = QHBoxLayout()
        expression_row.setSpacing(5)

        self.expression_label = QLabel("")

        self.expression_label.setAlignment(
            Qt.AlignmentFlag.AlignRight |
            Qt.AlignmentFlag.AlignVCenter
        )

        self.expression_label.setFont(
            QFont("Segoe UI", 15)
        )

        expression_row.addWidget(
            self.expression_label, 1
        )

        # Кнопка удаления

        self.backspace_btn = QPushButton("⌫")
        self.backspace_btn.setFixedSize(42, 38)

        self.backspace_btn.setFont(
            QFont("Segoe UI", 20)
        )

        self.backspace_btn.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )

        self.backspace_btn.clicked.connect(
            self.delete_last
        )

        expression_row.addWidget(self.backspace_btn)

        layout.addLayout(expression_row)

        # Экран результата

        self.display = QLabel("0")

        self.display.setAlignment(
            Qt.AlignmentFlag.AlignRight |
            Qt.AlignmentFlag.AlignVCenter
        )

        self.display.setMinimumHeight(95)

        self.display.setFont(
            QFont("Segoe UI", 42, QFont.Weight.Light)
        )

        layout.addWidget(self.display)

        layout.addSpacing(20)

        # Цифровая клавиатура

        keyboard = QGridLayout()
        keyboard.setSpacing(9)

        number_buttons = [
            ["C", "±", "%"],
            ["7", "8", "9"],
            ["4", "5", "6"],
            ["1", "2", "3"],
            [".", "0", "00"]
        ]

        for row, values in enumerate(number_buttons):

            for col, value in enumerate(values):

                button = QPushButton(value)

                button.setFixedSize(78, 72)

                button.setFont(
                    QFont("Segoe UI", 26, QFont.Weight.Light)
                )

                button.setObjectName("numberButton")

                button.setFocusPolicy(
                    Qt.FocusPolicy.NoFocus
                )

                button.clicked.connect(
                    lambda checked=False, v=value:
                    self.press(v)
                )

                self.buttons.append(button)

                keyboard.addWidget(button, row, col)

        # Вертикальная панель операций

        self.operator_panel = QFrame()
        self.operator_panel.setObjectName("operatorPanel")

        operator_layout = QVBoxLayout(self.operator_panel)

        operator_layout.setContentsMargins(5, 5, 5, 5)
        operator_layout.setSpacing(3)

        operators = ["+", "−", "×", "÷", "="]

        for value in operators:

            button = QPushButton(value)

            button.setFont(
                QFont("Segoe UI", 27, QFont.Weight.Light)
            )

            button.setMinimumHeight(65)

            button.setFocusPolicy(
                Qt.FocusPolicy.NoFocus
            )

            if value == "=":
                button.setObjectName("equalButton")
            else:
                button.setObjectName("operatorButton")

            button.clicked.connect(
                lambda checked=False, v=value:
                self.press(v)
            )

            operator_layout.addWidget(button)
            self.buttons.append(button)

        keyboard.addWidget(
            self.operator_panel,
            0, 3, 5, 1
        )

        layout.addLayout(keyboard)
        layout.addStretch(1)

        # Нижняя надпись

        self.footer = QLabel(
            "Liquid Glass  •  Python Edition"
        )

        self.footer.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(self.footer)

        # Загружаем тему

        saved_theme = self.settings.value(
            "theme", "dark"
        )

        if saved_theme not in THEMES:
            saved_theme = "dark"

        self.apply_theme(saved_theme)

    # ======================================
    # НАСТРОЙКИ
    # ======================================

    def open_settings(self):

        dialog = SettingsDialog(self)
        dialog.exec()

        self.setFocus()

    # ======================================
    # СМЕНА ТЕМЫ
    # ======================================

    def apply_theme(self, theme):

        if theme not in THEMES:
            theme = "dark"

        self.theme = theme
        self.settings.setValue("theme", theme)

        c = THEMES[theme]

        self.panel.setStyleSheet(f"""
            QFrame#glassPanel {{
                background: {c['panel']};
                border: 1px solid {c['border']};
                border-radius: 32px;
            }}
        """)

        self.drag_bar.title.setStyleSheet(f"""
            color: {c['text']};
            background: transparent;
            border: none;
        """)

        self.expression_label.setStyleSheet(f"""
            color: {c['text']};
            background: transparent;
            border: none;
        """)

        # Полностью прозрачный экран результата

        self.display.setStyleSheet(f"""
            color: {c['text']};
            background: transparent;
            border: none;
            padding: 10px;
        """)

        self.backspace_btn.setStyleSheet(f"""
            QPushButton {{
                background: {c['button']};
                color: {c['text']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}

            QPushButton:hover {{
                background: {c['hover']};
            }}
        """)

        self.footer.setStyleSheet(f"""
            color: {c['footer']};
            background: transparent;
            border: none;
            font-size: 11px;
        """)

        self.operator_panel.setStyleSheet(f"""
            QFrame#operatorPanel {{
                background: {c['operator']};
                border: 1px solid {c['border']};
                border-radius: 19px;
            }}
        """)

        for button in self.buttons:

            kind = button.objectName()

            if kind == "equalButton":

                button.setStyleSheet("""
                    QPushButton {
                        background: rgba(255,255,255,205);
                        color: #777777;
                        border: none;
                        border-radius: 13px;
                    }

                    QPushButton:hover {
                        background: white;
                    }

                    QPushButton:pressed {
                        background: rgba(220,220,220,220);
                    }
                """)

            elif kind == "operatorButton":

                button.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {c['text']};
                        border: none;
                        border-radius: 13px;
                    }}

                    QPushButton:hover {{
                        background: {c['operator_hover']};
                    }}
                """)

            else:

                button.setStyleSheet(f"""
                    QPushButton {{
                        background: {c['button']};
                        color: {c['text']};
                        border: none;
                        border-radius: 15px;
                    }}

                    QPushButton:hover {{
                        background: {c['hover']};
                    }}

                    QPushButton:pressed {{
                        background: {c['operator_hover']};
                    }}
                """)

        for button in (
            self.drag_bar.settings_btn,
            self.drag_bar.min_btn,
            self.drag_bar.close_btn
        ):

            button.setStyleSheet(f"""
                QPushButton {{
                    background: {c['button']};
                    color: {c['text']};
                    border: none;
                    border-radius: 10px;
                    font-size: 17px;
                }}

                QPushButton:hover {{
                    background: {c['hover']};
                }}
            """)

    # ======================================
    # ФОРМАТИРОВАНИЕ ЧИСЕЛ
    # ======================================

    def format_number(self, number):

        if isinstance(number, float):
            if number.is_integer():
                number = int(number)

        return f"{number:,}".replace(",", " ")

    # ======================================
    # ОБНОВЛЕНИЕ ЭКРАНА
    # ======================================

    def update_display(self):

        if not self.expression:
            self.display.setText("0")
        else:
            self.display.setText(self.expression)

    # ======================================
    # УДАЛЕНИЕ СИМВОЛА
    # ======================================

    def delete_last(self):

        self.expression = self.expression[:-1]

        self.just_calculated = False
        self.last_operator = None
        self.last_operand = None

        self.expression_label.setText("")
        self.update_display()

        self.setFocus()

    # ======================================
    # ОЧИСТКА
    # ======================================

    def clear_all(self):

        self.expression = ""
        self.just_calculated = False

        self.last_operator = None
        self.last_operand = None

        self.expression_label.setText("")
        self.update_display()

    # ======================================
    # ОБРАБОТКА КНОПОК
    # ======================================

    def press(self, value):

        if value == "C":

            self.clear_all()

        elif value == "=":

            self.solve()
            return

        elif value == "⌫":

            self.delete_last()
            return

        elif value in ["+", "−", "×", "÷"]:

            if self.expression:

                if self.just_calculated:
                    self.just_calculated = False

                if self.expression[-1] in "+−×÷":
                    self.expression = self.expression[:-1]

                self.expression += value

        elif value == "±":

            if self.expression:

                if self.just_calculated:
                    self.just_calculated = False
                    self.last_operator = None
                    self.last_operand = None

                match = re.search(
                    r'(\d+(?:\.\d*)?)$',
                    self.expression
                )

                if match:

                    start = match.start()
                    previous = self.expression[start - 1:start]

                    unary_minus = (
                        previous == "-"
                        and (
                            start - 1 == 0
                            or self.expression[start - 2:start - 1]
                            in "+−×÷("
                        )
                    )

                    if unary_minus:

                        self.expression = (
                            self.expression[:start - 1]
                            + self.expression[start:]
                        )

                    else:

                        self.expression = (
                            self.expression[:start]
                            + "-"
                            + self.expression[start:]
                        )

        elif value == "%":

            if self.expression:

                if self.just_calculated:
                    self.just_calculated = False
                    self.last_operator = None
                    self.last_operand = None

                match = re.search(
                    r'(\d+(?:\.\d*)?)$',
                    self.expression
                )

                if match:

                    number = match.group(1)

                    self.expression = (
                        self.expression[:match.start()]
                        + f"({number}/100)"
                    )

        elif value in [".", "0", "00"] or value.isdigit():

            if self.just_calculated:

                self.expression = ""
                self.just_calculated = False

                self.last_operator = None
                self.last_operand = None

            if len(self.expression) < 100:

                # Не допускаем несколько точек в одном числе
                if value == ".":
                    match = re.search(
                        r'(\d+\.?\d*)$',
                        self.expression
                    )

                    if match and "." in match.group(1):
                        return

                    if not self.expression or self.expression[-1] in "+−×÷":
                        self.expression += "0"

                self.expression += value

        self.expression_label.setText("")
        self.update_display()

        self.setFocus()

    # ======================================
    # ВЫЧИСЛЕНИЕ И ПОВТОР ПОСЛЕДНЕЙ ОПЕРАЦИИ
    # ======================================

    def solve(self):

        # Повторное нажатие "="

        if self.just_calculated:

            if self.last_operator is None:
                return

            try:

                operations = {
                    "+": operator.add,
                    "-": operator.sub,
                    "*": operator.mul,
                    "/": operator.truediv
                }

                current = float(self.expression)

                result = operations[self.last_operator](
                    current,
                    self.last_operand
                )

                if not math.isfinite(result):
                    raise ValueError("Некорректный результат")

                if abs(result) > 1e100:
                    raise ValueError("Слишком большое число")

                result = round(result, 10)

                if result.is_integer():
                    result = int(result)

                self.expression_label.setText(
                    f"{self.format_number(current)} "
                    f"{self.last_operator} "
                    f"{self.format_number(self.last_operand)} ="
                )

                self.expression = str(result)

                self.display.setText(
                    self.format_number(result)
                )

                self.just_calculated = True

            except Exception:

                self.display.setText("Ошибка")
                self.expression = ""
                self.just_calculated = False

                self.last_operator = None
                self.last_operand = None

            return

        if not self.expression:
            return

        try:

            expression = (
                self.expression
                .replace("×", "*")
                .replace("÷", "/")
                .replace("−", "-")
            )

            # Запоминаем последнюю операцию

            tree = ast.parse(
                expression,
                mode="eval"
            ).body

            operator_map = {
                ast.Add: "+",
                ast.Sub: "-",
                ast.Mult: "*",
                ast.Div: "/"
            }

            if isinstance(tree, ast.BinOp):

                op = operator_map.get(type(tree.op))

                if op is not None:

                    self.last_operator = op

                    self.last_operand = calculate(
                        ast.unparse(tree.right)
                    )

                else:

                    self.last_operator = None
                    self.last_operand = None

            else:

                self.last_operator = None
                self.last_operand = None

            # Основное вычисление

            result = calculate(expression)

            result = round(result, 10)

            if isinstance(result, float) and result.is_integer():
                result = int(result)

            self.expression_label.setText(
                self.expression + " ="
            )

            self.expression = str(result)

            self.display.setText(
                self.format_number(result)
            )

            self.just_calculated = True

        except Exception:

            self.display.setText("Ошибка")

            self.expression = ""
            self.expression_label.setText("")

            self.just_calculated = False
            self.last_operator = None
            self.last_operand = None

        self.setFocus()

    # ======================================
    # УПРАВЛЕНИЕ С КЛАВИАТУРЫ
    # ======================================

    def keyPressEvent(self, event):

        key = event.key()
        text = event.text()

        # Enter
        if key in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter
        ):
            self.press("=")
            return

        # Backspace
        if key == Qt.Key.Key_Backspace:
            self.delete_last()
            return

        # Delete и Escape
        if key in (
            Qt.Key.Key_Delete,
            Qt.Key.Key_Escape
        ):
            self.clear_all()
            return

        # Цифры
        if text and text in "0123456789":
            self.press(text)
            return

        # Операции
        key_map = {
            "+": "+",
            "-": "−",
            "*": "×",
            "/": "÷",
            "%": "%",
            ".": ".",
            ",": ".",
            "=": "="
        }

        if text in key_map:
            self.press(key_map[text])
            return

        if text.lower() == "c":
            self.clear_all()
            return

        super().keyPressEvent(event)


# ==========================================
# ЗАПУСК ПРОГРАММЫ
# ==========================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setApplicationName(
        "Liquid Glass Calculator"
    )

    window = GlassCalculator()

    window.show()
    window.setFocus()

    sys.exit(app.exec())
