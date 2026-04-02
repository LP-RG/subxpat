module abs_diff_i572_o286(a,b,r);
input [285:0] a,b;
output [285:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
