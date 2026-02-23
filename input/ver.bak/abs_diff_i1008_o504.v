module abs_diff_i1008_o504(a,b,r);
input [503:0] a,b;
output [503:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
