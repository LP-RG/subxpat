module madd_i6144_o4096 (a, b, c, r);
input [2047:0] a,b,c;
output [4095:0] r;

assign r = (a * b) + c;

endmodule
