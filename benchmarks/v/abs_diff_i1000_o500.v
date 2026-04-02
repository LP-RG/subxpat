module abs_diff_i1000_o500(a,b,r);
input [499:0] a,b;
output [499:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
