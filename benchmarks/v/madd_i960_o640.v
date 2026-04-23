module madd_i960_o640 (a, b, c, r);
input [319:0] a,b,c;
output [639:0] r;

assign r = (a * b) + c;

endmodule
