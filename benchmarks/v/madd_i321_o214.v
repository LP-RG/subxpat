module madd_i321_o214 (a, b, c, r);
input [106:0] a,b,c;
output [213:0] r;

assign r = (a * b) + c;

endmodule
