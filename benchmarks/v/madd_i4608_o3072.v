module madd_i4608_o3072 (a, b, c, r);
input [1535:0] a,b,c;
output [3071:0] r;

assign r = (a * b) + c;

endmodule
