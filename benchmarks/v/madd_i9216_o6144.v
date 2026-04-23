module madd_i9216_o6144 (a, b, c, r);
input [3071:0] a,b,c;
output [6143:0] r;

assign r = (a * b) + c;

endmodule
