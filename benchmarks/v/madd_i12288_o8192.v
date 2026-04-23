module madd_i12288_o8192 (a, b, c, r);
input [4095:0] a,b,c;
output [8191:0] r;

assign r = (a * b) + c;

endmodule
