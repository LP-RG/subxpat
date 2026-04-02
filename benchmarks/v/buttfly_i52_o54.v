module buttfly_i52_o54 (a,b,r1,r2);
input [25:0] a,b;
output [26:0] r1,r2;

assign r1 = a+b;

assign r2 = a-b;

endmodule
