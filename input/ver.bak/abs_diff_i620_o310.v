module abs_diff_i620_o310(a,b,r);
input [309:0] a,b;
output [309:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
