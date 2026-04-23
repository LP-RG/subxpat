module abs_diff_i6656_o3328(a,b,r);
input [3327:0] a,b;
output [3327:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
