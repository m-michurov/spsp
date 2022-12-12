# spsp

Spsp (read like **sp** in Li**sp** but twice) is a Lisp-like programming language
I made just for run.

Spsp doesn't have its own standard library but can use Python modules.

## Run

Run REPL:
```bash
$> python -m spsp
```

Run one or multiple `.spsp` file(s):
```bash
$> python -m spsp file1.spsp file2.spsp ...
```
Files will be executed in order within same global scope.

Run REPL after loading `.spsp` files by adding --repl in the end:
```bash
$> python -m spsp std-lib.spsp --repl
```
Run standard library `std-lib.spsp` before any of your files/REPL if you need more than just basic syntax.

## Features

### Symbolic expressions
```lisp
>>> (+ 1 2)
3
```
### List expressions

(evaluate to Python lists)
```lisp
>>> [+ 1 2]
[<function _plus at 0x00000260671583A0>, 1, 2]
```
### String literals
```lisp
>>> "hello, world!"
hello, world!
>>> 'hello, world!'
hello, world!
```
### Numeric literals
```lisp
>>> -42
-42
>>> +4.2e+1
42.0
```
### Boolean literals
```lisp
>>> [True, False]
[True, False]
```
### None literal
```lisp
>>> None
None
```
### Variables
```lisp
>>> (let x 41)
41
>>> x
41
>>> (let x (+ 1 x))
42
>>> x
42
```
### Destructuring assignment
```lisp
>>> (let y [1 [2 3]])
[1, [2, 3]]
>>> (let [a [b c]] y)
[1, [2, 3]]
>>> a b c
1
2
3
```
### Importing Python modules
```lisp
>>> (let types (import-module 'types'))
<module 'types' from 'C:\\DKs\\Python 3.10.7\\lib\\types.py'>
```
### Accessing attribute values
```lisp
>>> (let obj (types::SimpleNamespace))
namespace()
>>> (let obj::field 42)
42
>>> obj::field
42
```
### Removing value form scope or deleting attribute
```lisp
>>> (let x 42)
42
>>> x
42
>>> (del x)
None
>>> x
SpspNameError: x
>>> (del obj::field)
None
>>> obj::field
SpspAttributeError: (namespace(), 'field')
```
### Scope hierarchy
```lisp
>>> (let x 42)
42
>>> (do (let x 43) x)  ; Special form 'do' evaluates it's argumnts in a local scope
43
>>> x
42
```
### Anonymous functions
```lisp
>>> ((lambda [x] (+ 1 x)) 41)
42
```
### Closures
```lisp
>>> (let counter \
... 	(do \
... 		(let value [0]) \
...  		[(lambda [] (get value 0)) \
... 		 (lambda [] (set value 0 (+ 1 (get value 0))))]))
[(lambda [] (get value 0)), (lambda [] (set value 0 (+ 1 (get value 0))))]
>>> (let [get-val inc-val] counter)
[(lambda [] (get value 0)), (lambda [] (set value 0 (+ 1 (get value 0))))]
>>> (get-val)
0
>>> (inc-val)
None
>>> (get-val)
1
>>> value
SpspNameError: value
```
### Code as value
```lisp
>>> (let code (expr! (+ 1 2)))
(+ 1 2)
>>> (eval! code)
3
```
### Macros

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
### Variadic bindings
When using structured binding (in `let`, or when 
declaring function or macro parameters list), you can add
`& <rest>` (`<rest>` must be an identifier) at the end of target expression
list to bind any excess arguments to `<rest>`.

**Variadic `let` binding**
```lisp
>>> (let [x y & *rest] (range 10))
range(0, 10)
>>> x y *rest
0                       
1                       
(2, 3, 4, 5, 6, 7, 8, 9)
```
**Variadic functions**
```lisp
>>> (let int* (lambda [& *args] (list (map int *args))))
<spsp.evaluation.Function object at 0x000001A7887A6E00>
>>> (int* '1' '2' '42')
[1, 2, 42]
```
**Variadic macros**

*See [short-circuit logical and example](examples/macro-short-circuit-and.spsp)*.

## Python interoperability

Spsp is built upon Python runtime.

As a result, you have the entirety of Python's standard library at your disposal.

### Call python functions and methods

Calling Python functions

```lisp
>>> (list (range 10))
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

Calling methods

```lisp
>>> (str::upper 'hello world!')
HELLO WORLD!
>>> (let s 'hello world!')
hello world!
>>> (s::capitalize)
Hello world!
>>> (s::find 'wo')
6
```

Passing spsp functions to python functions as parameters

```lisp
>>> (let even? (lambda [x] (= 0 (% x 2))))
Lambda [x]
>>> (list (filter even? (range 10)))
[0, 2, 4, 6, 8]
```

## Special forms

*List of existing special forms coming soon*

## Predefined identifiers

Call `predefined` to get a list of all predefined identifiers
not including special forms.

```lisp
>>> (predefined)
['+', '-', '*', '/', '//', '**', '%', 'import-module', 'first', 'rest', 'call', 'doc', '<', '<=', '>', '>=', '=', 'is', 'is-not', 'not', 'contains', 'predefined', 'set', 'get']
```

*List of existing predefined identifiers coming soon*

## Examples

See [examples](examples).
