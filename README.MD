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

Run REPL after loading `.spsp` files by adding `--repl` in the end:
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

### Exceptions

Raise Python exceptions using `raise`:
```lisp
>>> (let n -1)
-1  
>>> (when (< n 0)
...   (raise (ValueError 'Expected non-negative')))
File "<stdin>", line 1
(when (< n 0)         
^                     
ValueError: Expected non-negative
```

Catch exceptions using `try` macro.
Syntax is as follows:
```lisp
; With 'finally'
(try
    <body>
    (except <exception-binding> <except-body>)
    (finally <finally-body>))
    
; Without 'finally'
(try
    <body>
    (except <exception-binding> <except-body>))
```
`try` evaluates `<body>` in a local context and returns its value.
If `<body>` throws an exception, result of `<except-body>` is returned
instead. `finally`, if present, is always evaluated last.

Example usage:
```lisp
>>> (try                                                  
...   (/ 10 0)                     
...   (except e (print (getattr (type e) '__name__') ':' e)))  
ZeroDivisionError : division by zero
None
>>> (try
...   (/ 10 0)
...   (except _ -1)
...   (finally (print 'finally')))
finally
-1
```

### Lazy evaluation and non-strict functions

Python functions are always strict in all of their
parameters, i.e. their 
arguments are evaluated before the function is executed.
Spsp functions, however, can be both strict and 
non-strict in their arguments, depending on how 
arguments are passed. 

To delay evaluation, use `lazy` macro:
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

Passing an argument as `lazy` in a function invocation
will make the function behave as non-strict in that
argument.

Consider this definition of function `use`:
```lisp
>>> (def use [x]                              
...     (do 
...     (print 'Using provided value')
...     (print (+ 1 x))))
<spsp.evaluation.Function object at 0x000001AA3B528760>
```
`use` can behave as strict in `x`:
```lisp
>>> (use (do (print 'Evaluating') 41))                 
Evaluating          
Using provided value
42                  
None                
```
But can also behave as non-strict:
```lisp
>>> (use (lazy (do (print 'Evaluating') 41)))
Using provided value
Evaluating          
42                  
None                
>>> 
```
`lazy`'s body is evaluated only once, value is cached:
```lisp
>>> (let x (lazy (do (print 'Evaluating') 41))) 
<spsp.lazy.Lazy object at 0x000001AA3B52AA40>
>>> (print x)                                   
Evaluating
41        
None      
>>> (print x)
41  
None
```
Nested `lazy` expressions behave as a single-level `lazy`:
```lisp
>>> (let x (lazy 42))
<spsp.lazy.Lazy object at 0x000001AA3B52A4D0>
>>> (let y (lazy (lazy x)))                  
<spsp.lazy.Lazy object at 0x000001AA3B529CC0>
>>> (print y)                                
42  
None
```
If a `lazy` is used as the first item in a
symbolic expression, it is always evaluated:
```lisp
>>> (let plus (lazy (do (print '"plus"') +)))
<spsp.lazy.Lazy object at 0x000001AA3B77C3D0>
>>> (plus                                    
...   (do (print 1) 1)
...   (do (print 2) 2))
"plus"
1
2
3
```

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

*List of existing predefined identifiers coming soon*

## Examples

See [examples](examples).
