Store_column 	equ 30H
Store_row 		equ 31H

org 0000H

MAIN:
	; Column scan
		; P1.7-P1.4 (Rows)    = 0 (Ground)
		; P1.3-P1.0 (Columns) = 1 (Input/Pull-up)
	mov P1, #0FH
	mov Store_column, P1
	
	; Row scan
		; P1.7-P1.4 (Rows)    = 1 (Input/Pull-up)
		; P1.3-P1.0 (Columns) = 0 (Ground)
	mov P1, #0F0H
	mov Store_row, P1
	
	; Combine and display
	mov A, Store_column
	orl A, Store_row
	mov P2, A
sjmp MAIN

end