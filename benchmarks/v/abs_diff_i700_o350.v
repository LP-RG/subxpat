module abs_diff_i700_o350(a,b,r);
input [349:0] a,b;
output [349:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
