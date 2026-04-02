module madd_i252_o168 (a, b, c, r);
input [83:0] a,b,c;
output [167:0] r;

assign r = (a * b) + c;

endmodule
