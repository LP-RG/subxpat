module madd_i255_o170 (a, b, c, r);
input [84:0] a,b,c;
output [169:0] r;

assign r = (a * b) + c;

endmodule
