module madd_i1152_o768 (a, b, c, r);
input [383:0] a,b,c;
output [767:0] r;

assign r = (a * b) + c;

endmodule
