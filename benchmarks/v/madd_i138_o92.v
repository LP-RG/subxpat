module madd_i138_o92 (a, b, c, r);
input [45:0] a,b,c;
output [91:0] r;

assign r = (a * b) + c;

endmodule
