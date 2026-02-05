Pin_EN equ P2.7
Pin_RS equ P2.6
Pin_WR equ P2.5

org 0000H
	
LOOP:	
	mov A, #38H
	acall WRITE_COMMAND
	
	mov A, #0CH
	acall WRITE_COMMAND
	
	mov A, #01H
	acall WRITE_COMMAND
	
	mov A, #'H'
	acall WRITE_DATA
	
	mov A, #'i'
	acall WRITE_DATA
	
	mov A, #'.'
	acall WRITE_DATA
	
	sjmp $

WRITE_COMMAND:
	mov P0, A
	clr Pin_RS
	clr Pin_WR
	setb Pin_EN
	clr Pin_EN
	acall DELAY
	ret

WRITE_DATA:
	mov P0, A
	setb Pin_RS
	clr Pin_WR
	setb Pin_EN
	clr Pin_EN
	acall DELAY
	ret

DELAY:
	mov R3, #10
	DELAY_STOP_2: mov R4, #255
	DELAY_STOP: djnz R4, DELAY_STOP
	djnz R3, DELAY_STOP_2
	ret
end