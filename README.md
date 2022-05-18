This module makes significant use of code from the CPython project. In summary:

 - the `int`, `float`, `bool`, `tuple` and `none` object implimentations have been extracted from CPython and modified to work with this project
   - this primarily involved rewriting macros and utility functions to no longer depend on the rest of the interpreter
 - the `type` object has had some new fields added to it, representing non-rich comparisons
 - all exception handling has been removed, and raising an exception causes the program to print an error and then exit.

The code found in `c/include/cpython/*`, `c/Objects/*`, as well as `c/include/object.h`, all contain significant 
amounts of code which has been modified from the original source in some way, as well as original code.

Below is the PSF's notice of copyright, which applies only to code derived from the CPython project:

> Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 
> 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022 
> Python Software Foundation; All Rights Reserved

A copy of the PSF licence is included below, for reference. 
It applies only to code derived from CPython; all other code is under the MIT licence, also included below.

## PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2

1. This LICENSE AGREEMENT is between the Python Software Foundation
   ("PSF"), and the Individual or Organization ("Licensee") accessing and
   otherwise using this software ("Python") in source or binary form and
   its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
   grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
   analyze, test, perform and/or display publicly, prepare derivative works,
   distribute, and otherwise use Python alone or in any derivative version,
   provided, however, that PSF's License Agreement and PSF's notice of copyright,
   i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
   2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022 Python Software Foundation;
   All Rights Reserved" are retained in Python alone or in any derivative version
   prepared by Licensee.

3. In the event Licensee prepares a derivative work that is based on
   or incorporates Python or any part thereof, and wants to make
   the derivative work available to others as provided herein, then
   Licensee hereby agrees to include in any such work a brief summary of
   the changes made to Python.

4. PSF is making Python available to Licensee on an "AS IS"
   basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
   IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
   DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
   FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
   INFRINGE ANY THIRD PARTY RIGHTS.

5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
   FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
   A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
   OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

6. This License Agreement will automatically terminate upon a material
   breach of its terms and conditions.

7. Nothing in this License Agreement shall be deemed to create any
   relationship of agency, partnership, or joint venture between PSF and
   Licensee.  This License Agreement does not grant permission to use PSF
   trademarks or trade name in a trademark sense to endorse or promote
   products or services of Licensee, or any third party.

8. By copying, installing or otherwise using Python, Licensee
   agrees to be bound by the terms and conditions of this License
   Agreement.

## MIT licence

Copyright 2022 [redacted]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.