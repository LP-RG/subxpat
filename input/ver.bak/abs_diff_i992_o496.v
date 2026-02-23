module abs_diff_i992_o496(a,b,r);
input [495:0] a,b;
output [495:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
