module abs_diff_i456_o228(a,b,r);
input [227:0] a,b;
output [227:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
