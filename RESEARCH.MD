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

С помощью макроса `def` ([определение](std-lib.spsp#L58-L63)) 
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
`import` ([определение](std-lib.spsp#L65-L70)):
```lisp
(import functools)

(let total (functools::reduce + [1 2 3] 0))
(print total)
```

Есть еще `import-from` 
([определение](std-lib.spsp#L72-L80)):
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

Логические связки `and` ([определение](std-lib.spsp#L32-L43)) и `or` ([определение](std-lib.spsp#L45-L56)) реализованы через макросы. Они получаются ленивые, потому что 
макросы принимают аргументы без вычисления, а внутри аргументы вычисляются только если нужно.

```lisp
(let and
    (macro [op1 & *rest]
        (do
            (let functools (import-module 'functools'))
            (expr!
                ((inline-value! functools::reduce)
                    (lambda [result expr]
                        (if result
                            (bool (eval! expr))
                            (bool result)))
                    (inline-value! *rest)
                    (bool (inline! op1)))))))
```

Пример с конъюнкцией:
```lisp
>>> (print
...     'Result:'
...     (and
...         (do (print 'Evaluated op #1:' 1) 1)
...         (do (print 'Evaluated op #2:' False) False)
...         (do (print 'Evaluated op #3:' [1 2 3]) [1 2 3])))
Evaluated op #1: 1
Evaluated op #2: False
Result: False
None
```

## Цикл либо оптимизированная хвостовая рекурсия

Цикл `for` ([определение](std-lib.spsp#L82-L91)) реализован через макрос
```lisp
(let for 
    (macro [var coll body] 
        (do 
            (let functools (import-module 'functools'))
            (let body-fn (eval! (expr! (lambda [(inline! var)] (inline! body)))))
            (expr! 
                ((inline-value! functools::reduce)
                    (lambda [a b] None) 
                    (map (inline-value! body-fn) (inline! coll))
                    None)))))
```

Пример использования цикла:
```lisp
>>> (let evens [])
[]
>>> (for i (range 10)
...     (when (= 0 (% i 2))
...         (evens::append i)))
None
>>> evens
[0, 2, 4, 6, 8]
```

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

Ключевое слово `raise` используется для генерации исключений.

Пример:
```lisp
>>> (let n -1)
-1
>>> (when (< n 0) (raise (ValueError "Число n должно быть положительным")))
File "<stdin>", line 1
(when (< n 0) (raise (ValueError "Число n должно быть положительным")))
^
ValueError: Число n должно быть положительным
```

Конструкция `try` используется для обработки исключений. Она 
реализована через макрос:
```lisp
(let try
    (macro [body handler & finally]
        (do
            (when (!= (getattr (first handler) "name") "except")
                (raise (ValueError 'Exception handler should start with "except"')))
            (let finally
                (if finally
                    (first finally)
                    (expr! (finally None))))
            (when (!= (getattr (first finally) "name") "finally")
                (raise (ValueError 'Finally statement should start with "finally"')))
            (let exception-identifier (second handler))
            (expr!
                (run-catching
                    (lambda [] (inline! body))
                    (lambda [(inline! exception-identifier)] (inline! (last handler)))
                    (lambda [] (inline! (second finally))))))))
```

Для реализации `try` была написана встроенная в интерпретатор
функция `run-catching`.
Она принимает функцию (`body`), которая может выбросить исключение, 
функцию-обработчик (`handler`) и функцию (`finally`), вызывающуюся в конце.

Пример:
```lisp
>>> (try (/ 10 0)
...      (except ex (print ex))
...      (finally (print "Finally")))
division by zero
Finally
None
```

`try` можно использовать и без `finally`, например:
```lisp
>>> (try (/ 10 0)
...      (except _ 0))
0
```

## Для чисто-функционального Lisp

### Ленивые вычисления

В принципе, обеспечивается итераторами из Python. Те же 
`map` и `filter` в Python ленивые.

### Отложенный порядок вычислений для вызовов функций

В книге "Структура и интерпретация компьютерных программ" в 
разделе 4.2.1 говорится про принцип реализации ленивых
вычислений:
```commandline
В разделе 1.1, где мы начали обсуждение моделей вычисления, мы указали, что
Scheme — язык с аппликативным порядком вычисления (applicative-order language), а
именно, что все аргументы процедур в Scheme вычисляются в момент вызова. Напротив,
в языках с нормальным порядком вычисления (normal-order language) вычисление аргументов 
процедур задерживается до момента, когда действительно возникает нужда в
их значениях. Если вычисление аргументов процедур откладывается как можно дольше
(например, до того момента, когда они требуются какой-либо элементарной процедуре),
то говорят о ленивом вычислении (lazy evaluation). 

Если тело процедуры начинает выполняться прежде, чем вычисляется ее аргумент, то
процедура называется нестрогой (non-strict) по этому аргументу. Если же аргумент 
вычисляется прежде, чем происходит вход в процедуру, то процедура называется строгой
(strict) по этому аргументу. В чисто аппликативном языке все процедуры строги по
всем своим аргументам. В языке с чисто нормальным порядком вычислений все составные 
процедуры нестроги по всем своим аргументам, а элементарные процедуры могут
быть и такими, и такими.
```

Отсюда появилась идея реализовать ленивые вычисления за счет реализации
нормального порядка вычисления в нашем языке, то есть ленивые объекты, переданные в 
качестве аргументов функции, вычислять не сразу, а только когда они понадобятся.
Python же будет вычислять аргументы функции до выполнения тела функции, то есть
работать аппликативно. Таким образом, Python-функции строгие по всем аргументам, 
а Spsp-функции - строгие по всем аргументам по умолчанию, но нестрогие по аргументам, переданным как `lazy`.

Класс `Lazy` хранит значение выражения и функцию, 
которая будет вычислена при первом обращении:
```py
@dataclass(repr=False)
class Lazy:
    _eval: Callable[[], Any]
    _value: Any = NOT_EVALUATED

    @property
    def value(self) -> Any:
        if self._value is not NOT_EVALUATED:
            return self._value

        self._value = self._eval()
        if isinstance(self._value, Lazy):
            return self._value.value
        return self._value
```

Отложенный порядок вычисления можно использовать с помощью макроса
`lazy`:
```lisp
(let lazy
	(macro [body]
		(expr!
		    (make-lazy (lambda [] (inline! body))))))
```

`make-lazy` просто возвращает объект типа `Lazy`:
```py
@define(Keyword.MakeLazy)
def _make_lazy(
        body: Callable[[], Any]) -> Any:
    return Lazy(body)
```

Когда дело доходит до вычисления Pyhton-функций
все аргументы типа `Lazy` заменяются на их значения.

Пример:
```lisp
>>> (let x 42) 
42  
>>> (let y (lazy (do (print "Calc y") (+ 1 x)))) 
<spsp.lazy.Lazy object at 0x000001A0A2DF1090>
>>> (let z (lazy (do (print "Calc z") (* 2 y)))) 
<spsp.lazy.Lazy object at 0x000001A0A2DF1C50>
>>> (let t (lazy (do (print "Calc t") (- z y)))) 
<spsp.lazy.Lazy object at 0x000001A0A2DF2810>
>>> (print t)  
Calc t
Calc z
Calc y
43    
None 
```

При повторном обращении к переменной она не будет вычисляться заново:
```lisp
>>> (def use [x]                                                     
...   (do                                                            
...     (print 'amogus') 
...     (print (+ 1 x))))
<spsp.evaluation.Function object at 0x000002067F171010>
>>> (let y (lazy (do (import time) (print 'hard function') (time::sleep 5) 41)))
<spsp.lazy.Lazy object at 0x000002067F171F50>
>>> (use y)                                  
amogus       
hard function
42
None
>>> (use y)
amogus
42    
None  
>>>  
```

Если значением объекта типа `Lazy` является другой объект типа `Lazy`,
то при вычислении первого все последующие также будут вычислены:
```lisp
>>> (let y (lazy (lazy (lazy 41))))
<spsp.lazy.Lazy object at 0x000001BF2EDB0C90>
>>> (+ y 1)                                  
42  
```

## Динамические лексические контексты (по аналогии с binding в Clojure)

Пример из clojure ([ссылка](https://clojuredocs.org/clojure.core/binding)):
```lisp
;; Here are the definitions.
(defn mymax [x y]
  (min x y))

(defn find-max [x y]
  (max x y))

user=> (let [max mymax]
         (find-max 10 20))

20 ;let is ineffective outside current lexical scope


user=> (binding [max mymax]
         (find-max 10 20))

10 ;because max is now acting as min
```

Как это у нас:
```lisp
>>> (def mymax [x y] (min x y))
<spsp.evaluation.Function object at 0x000001CD26E6E250>
>>> (def find-max [x y] (max x y)) 
<spsp.evaluation.Function object at 0x000001CD26E6ED50>
>>> (do (let max mymax) (find-max 10 20))
20
>>> (binding max mymax (find-max 10 20))  
10
>>>
```

`binding` реализован через макрос и использует ключевое слово `rebind`,
которое позволяет изменить значение переменной в родительской области
видимости.

Пример:
```lisp
>>> (let sum 0)
0
>>> (for i [1 2 3] (rebind sum (+ sum i)))
None
>>> sum
6
```

## Механизм, подобный макросу, но генерирующий не Lisp-код, а непосредственно код для платформы исполнения

**[TODO]**
