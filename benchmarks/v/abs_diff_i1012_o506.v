module abs_diff_i1012_o506(a,b,r);
input [505:0] a,b;
output [505:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
