module abs_diff_i212_o106(a,b,r);
input [105:0] a,b;
output [105:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
