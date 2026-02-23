module madd_i330_o220 (a, b, c, r);
input [109:0] a,b,c;
output [219:0] r;

assign r = (a * b) + c;

endmodule
