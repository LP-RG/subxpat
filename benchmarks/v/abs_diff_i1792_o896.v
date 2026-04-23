module abs_diff_i1792_o896(a,b,r);
input [895:0] a,b;
output [895:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
