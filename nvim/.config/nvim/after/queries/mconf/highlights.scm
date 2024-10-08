(string) @string

(escape_sequence) @string.escape

(number) @number

(comment) @comment

(bool) @boolean

(null) @constant

(assignment
  key: (_) @property)

(import) @keyword

(import
  key: (_) @constant)

(constant) @constant

[
 "["
 "]"
 "{"
 "}"
] @punctuation.bracket

[
 "="
 ":"
 ","
 "."
 "?"
 "~"
 "|"
] @punctuation.delimiter
