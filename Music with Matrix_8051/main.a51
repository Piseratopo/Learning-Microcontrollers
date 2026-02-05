Column_pos equ 30H
Row_pos equ 31H

org 0000H
	
LOOP:
	; === Checking with column is pressed ===
	; Return column 0 if the pressed button is on this column or no button is pressed.
	mov P1, #0FH
	mov R0, P1
	CHECK_COL_2:
		cjne R0, #1011B, CHECK_COL_3
		mov Column_pos, #2
		sjmp END_CHECK_COL
	CHECK_COL_3:
		cjne R0, #1101B, CHECK_COL_4
		mov Column_pos, #3
		sjmp END_CHECK_COL
	CHECK_COL_4:
		cjne R0, #1110B, CHECK_COL_1
		mov Column_pos, #4
		sjmp END_CHECK_COL
	CHECK_COL_1:
		cjne R0, #0111B, NO_PRESS
		mov Column_pos, #1
		sjmp END_CHECK_COL
	NO_PRESS:
		mov Column_pos, #0
	END_CHECK_COL:
	
	; === Checking with row is pressed ===
	mov P1, #0F0H
	mov R0, P1
	
	CHECK_ROW_2:
		cjne R0, #10110000B, CHECK_ROW_3
		mov Row_pos, #1
		sjmp END_CHECK_ROW
	CHECK_ROW_3:
		cjne R0, #11010000B, CHECK_ROW_4
		mov Row_pos, #2
		sjmp END_CHECK_ROW
	CHECK_ROW_4:
		cjne R0, #11100000B, CHECK_ROW_1
		mov Row_pos, #3
		sjmp END_CHECK_ROW
	CHECK_ROW_1:
		mov Row_pos, #0
	END_CHECK_ROW:
	
	; === Combining column and row checks to get the button's position ===
	
	mov A, Row_pos
	mov B, #4
	mul AB
	add A, Column_pos
	cpl A ; Display on the LED bar through P2
	mov P2, A
		

END_LOOP:
	ljmp LOOP

end