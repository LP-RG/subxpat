module abs_diff_i668_o334(a,b,r);
input [333:0] a,b;
output [333:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
