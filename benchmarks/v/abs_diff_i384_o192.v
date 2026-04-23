module abs_diff_i384_o192(a,b,r);
input [191:0] a,b;
output [191:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
