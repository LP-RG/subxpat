module abs_diff_i632_o316(a,b,r);
input [315:0] a,b;
output [315:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
