module madd_i36_o24 (a, b, c, r);
input [11:0] a,b,c;
output [23:0] r;

assign r = (a * b) + c;

endmodule
