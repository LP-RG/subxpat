module madd_i63_o42 (a, b, c, r);
input [20:0] a,b,c;
output [41:0] r;

assign r = (a * b) + c;

endmodule
