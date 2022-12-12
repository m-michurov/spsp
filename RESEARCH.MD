# Откуда есть пошел язык программирования Spsp

Давно хотелось сделать плюс-минус полноценный ЯП,
но очень не хотелось возиться со стандартной библиотекой.
Поэтому возникла идея: сделать Lisp-образную обертку над Python.
Отсюда возможность использовать практически все, что есть в Python, 
и стиль именования некоторых штук.

# Необходимые элементы

В примерах будет вперемешку копипаста из REPL'а (со всякими `>>>` 
и выводом) и обычный код на **Spsp**. Надеюсь, будет понятно, где что. 

## Определение функции

Есть анонимные функции, определяются с помощью специальной
формы `lambda` (на манер Python):
```lisp
>>> (lambda [x] (+ x 1))
<spsp.evaluation.Function object at 0x00000276B2E1E530>
>>> ((lambda [x] (+ x 1)) 41)                          
42 
```

Анонимную функцию можно присвоить переменной:
```lisp
>>> (let inc (lambda [x] (+ x 1)))
<spsp.evaluation.Function object at 0x00000276B2E1F0A0>
>>> (inc 41)
42
```

С помощью макроса `def` 
([examples/macro-def.spsp](examples/macro-def.spsp)) 
можно определить функцию более привычным образом:
```lisp
(def fib
    [n]
    (if (<= n 2)
        1
        (+ (fib (- n 1)) (fib (- n 2)))))
```


## Определение статического лексического контекста (let)

Изначально хотелось сделать не лексический контекст, а обычные 
переменные. Поэтому в **Spsp** специальная форма `let` сознает 
обыкновенную переменную, либо изменяет значение существующей.
`let` также используется для присваивания значений аттрибутам 
объектов:
```lisp
>>> (let obj (types::SimpleNamespace))
namespace()
>>> (let obj::field 42)
42
>>> obj::field
42
```

`let` работает с переменными в текущей области видимости и не может
присвоить значение переменной в родительской области видимости:
```lisp
>>> (let x 42)
42  
>>> (do
...     (print x)
...     (let x (+ x 1))
...     (print x))
42  
43  
None
>>> x
42  
```
Тут используется специальная форма `do`, которая позволяет 
в явном виде создать локальную область видимости.

**[TODO]** 
Аналог `let` из Clojure может быть реализован с помощью макроса 
как комбинация `do` и `let`, и выглядеть, например, так:
```lisp
(let-do
    [x y] [1 2]
    (print (+ x y))
```
При этом разворачиваться в:
```lisp
(do
    (let [x y] [1 2])
    (print (+ x y))
```

## Рекурсия

Рекурсия в **Spsp** работает благодаря тому, что все функции являются
замыканиями.
При объявлении анонимной функции (`lambda`), сохраняется ссылка
на область видимости, в которой функция была создана.
Все последующие изменения в этой области видимости также будут видны
в теле функции, что позволяет написать, например, следующий код:
```lisp
>>> (let fib
...     (lambda [n]
...         (if (<= n 2)
...             1
...             (+ (fib (- n 1)) (fib (- n 2))))))
<spsp.evaluation.Function object at 0x0000020E6644F5B0>
>>> (list (map fib (range 1 10))) 
[1, 1, 2, 3, 5, 8, 13, 21, 34]
```

Оптимизации хвостовой рекурсии нет, но можно 
сделать цикл (об этом позже).

## Доступ к вызовам платформы (кроме native assembler)

Он есть. Без каких-либо дополнительных 
действий можно использовать все, что есть в модуле `builtins`
Python.
Из предыдущего примера:
```lisp
>>> (list (map fib (range 1 10))) 
[1, 1, 2, 3, 5, 8, 13, 21, 34]
```
Здесь `list`, `map` и `range` - Python-объекты. 
Также этот пример иллюстрирует тот факт, что **Spsp**-функции 
можно использовать там, где ожидает функции Python 
(`fib` передается в `map`).

Используя `import-module`, можно импортировать 
другие модули Python по их именам:
```lisp
>>> (let types (import-module 'types'))
<module 'types' from 'C:\\DKs\\Python 3.10.7\\lib\\types.py'>
```
И после обращаться к объектам из модуля как к аттрибутам 
этого модуля:
```lisp
>>> (let obj (types::SimpleNamespace))
namespace()
```

Для удобства, `import-module` может быть обернуто в макрос
`import` ([examples/macro-import.spsp](examples/macro-import.spsp)):
```lisp
(import functools)

(let total (functools::reduce + [1 2 3] 0))
(print total)
```

Есть еще `import-from` 
([examples/macro-import-from.spsp](examples/macro-import-from.spsp)):
```lisp
(import-from functools [reduce partial])

(let inc (partial + 1))
(let one-to-ten (map inc (range 10)))

(print (reduce + one-to-ten 0))
```

## Ветвление, логические связки с отложенным порядком исполнения

Ветвление реализовано через специальную форму `if`:
```lisp
>>> (let print-count 
...     (lambda [coll]
...         (if coll
...             (print 'a lot')
...             (print 'empty'))))
<spsp.evaluation.Function object at 0x0000020E66464640>
>>> (print-count [1 2 3])
a lot
None
>>> (print-count [])      
empty
None
```
Правила определения истинности объекта такие же как в Python.

**[TODO]** Логические связки будут реализованы через макросы.

## Цикл либо оптимизированная хвостовая рекурсия

**[TODO]** Цикл может быть реализован через макрос.
В [macro-for.spsp](examples/macro-for.spsp) есть пример,
как это могло бы выглядеть, но необходимость создавать список
по числу итераций - как-то не очень, поэтому в итоге оно будет 
выглядеть и работать получше.

## Присваивание для символов в определении let (императивный Lisp), либо для отдельного примитива, аналогичного atom в Clojure (чисто функциональный Lisp)

**[TODO]** Не совсем понятно, о чем тут речь. Возможно, это именно
то, что сейчас делает `let`.

## Макрос

Макросы объявляются с помощью специальной формы `macro`.
При их использовании аргументы передаются без вычисления, 
а возвращаемое значение интерпретируется как выражение и 
вычисляется в той области видимости, где макрос был вызван.

В остальном макросы аналогичны функциям.

Далее описание макросов из [README.MD](README.MD):

A macro is a function that receives its arguments without 
evaluation (as expressions) and must return an expression.
```lisp
>>> (let print-expr (macro [e] (do (print e) (expr! None))))
(macro [e] (do (print e) (expr! None)))
>>> (print-expr (+ 1 2))
(+ 1 2)
None
>>> (print-expr [x y])
[x y]
None
```
When macro is called, the expression it returns is evaluated.

#### `inline!` and `inline-value!`

Inside `expr!` argument, you can use `inline!` to inject an expression 
object as-is. Here, macro `when` receives a condition expression (`cond`)
and code to be executed when condition is true (`body`) 
and returns an `if` statement.
```lisp
>>> (let when (macro [cond body] (expr! (if (inline! cond) (inline! body) None))))
(macro [cond body] (expr! (if (inline! cond) (inline! body) None)))
>>> (when True 42)
42
>>> (when False 42)
None
```

To inject an object value (not expression), use `inline-value!`.
Here, macro `import` receives an identifier expression, 
imports a module with corresponding name 
(`(import-module module-name::name)`),
and then injects module object as a value to assign to `module-name`
identifier.
```lisp
>>> (let import \
...     (macro [module-name] \
... 		(do \
...             (let module (import-module module-name::name)) \
...             (expr! \
...                 (let (inline! module-name) (inline-value! module))))))
(macro [module-name] (do (let module (import-module module-name::name)) (expr! (let (inline! module-name) (inline-value! module)))))
>>> (import types)
<module 'types' from 'C:\\DKs\\Python 3.10.7\\lib\\types.py'>
>>> 
```

## Ввод-вывод

Используется ввод-вывод из Python.
```lisp
>>> (print (str::upper (input)))
hello world!
HELLO WORLD!
None
```

# Дополнительные требования

## Генерация и обработка исключений (совместимых с исключениями платформы исполнения)

**[TODO]**

## Для чисто-функционального Lisp

### Ленивые вычисления

В принципе, обеспечивается итераторами из Python. Те же 
`map` и `filter` в Python ленивые.

### Отложенный порядок вычислений для вызовов функций

**[TODO]**

## Динамические лексические контексты (по аналогии с binding в Clojure)

**[TODO]**

## Механизм, подобный макросу, но генерирующий не Lisp-код, а непосредственно код для платформы исполнения

**[TODO]**