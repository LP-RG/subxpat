module madd_i78_o52 (a, b, c, r);
input [25:0] a,b,c;
output [51:0] r;

assign r = (a * b) + c;

endmodule
