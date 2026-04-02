module abs_diff_i856_o428(a,b,r);
input [427:0] a,b;
output [427:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
