module madd_i195_o130 (a, b, c, r);
input [64:0] a,b,c;
output [129:0] r;

assign r = (a * b) + c;

endmodule
