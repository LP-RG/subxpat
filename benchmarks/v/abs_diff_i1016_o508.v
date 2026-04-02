module abs_diff_i1016_o508(a,b,r);
input [507:0] a,b;
output [507:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
