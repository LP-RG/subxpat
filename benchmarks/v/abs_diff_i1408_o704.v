module abs_diff_i1408_o704(a,b,r);
input [703:0] a,b;
output [703:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
