module madd_i7680_o5120 (a, b, c, r);
input [2559:0] a,b,c;
output [5119:0] r;

assign r = (a * b) + c;

endmodule
