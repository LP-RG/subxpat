module abs_diff_i1664_o832(a,b,r);
input [831:0] a,b;
output [831:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
